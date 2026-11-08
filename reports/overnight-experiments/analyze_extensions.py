"""Replay and report the separately versioned Terra/evidence experiments."""

import argparse
import asyncio
import csv
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import mean

from swarm_lab.evacuation.dataset import Scenario
from swarm_lab.evacuation.evidence import EvidenceGame
from swarm_lab.evacuation.language import LanguageGame

ORDER = {"terra": 0, "4": 1, "5": 2}


def load(path):
    return (
        [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    )


def canonical(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False)


async def audit(folder, packs, models):
    m = json.loads((folder / "manifest.json").read_text())
    metadata = [
        c for c in load(folder / "calls.jsonl") if c["type"] == "provider_metadata"
    ]
    responses = [
        c for c in load(folder / "calls.jsonl") if c["type"] == "model_response"
    ]
    traces = load(folder / "traces.jsonl")
    model, provider, provider_name, prompt_price, completion_price = models[
        m["model_tag"]
    ]
    errors = []
    for c in metadata:
        p = c.get("requested_provider", {})
        if (
            c.get("model") != model
            or c.get("upstream_provider") != provider_name
            or c.get("requested_reasoning_effort") != "low"
            or c.get("requested_temperature") is not None
            or c.get("finish_reason") != "stop"
            or p.get("only") != [provider]
            or p.get("allow_fallbacks") is not False
            or p.get("max_price")
            != {"prompt": prompt_price, "completion": completion_price}
            or (
                m["model_tag"] == "terra"
                and p.get("ignore") != ["openai/flex", "openai/fast"]
            )
        ):
            errors.append("routing_generation_mismatch")
    s = Scenario(**m["scenario"])
    if m["section"] == "terra":
        game = LanguageGame(s, m["language"], packs[m["language"]])
    else:
        game = EvidenceGame(
            s,
            m["language"],
            packs[m["language"]],
            evidence="private" if m["section"] == "5" else m["arm"],
            forwarding="proof" if m["arm"] == "private_proof" else "text_only",
        )
    used = 0
    initial_receipts = (
        {
            i: 0
            for i in range(10)
            if i != game.source and game.known_capsules(game.state.histories[i])
        }
        if isinstance(game, EvidenceGame)
        else {}
    )
    first_decision, first_action = {}, {}
    first_joint, first_joint_action, joint_ids = {}, {}, {}
    first_false_decision = {}

    class Replay:
        async def decide(self, view):
            nonlocal used
            c = responses[used]
            used += 1
            if canonical(c["view"]) != canonical(view):
                raise ValueError("response_view_mismatch")
            raw = c["raw"].strip()
            if raw.startswith("```json\n") and raw.endswith("\n```"):
                raw = raw[8:-4].strip()
            return json.loads(raw)

    rounds = []
    try:
        for t in traces:
            known = [
                int(i)
                for i, v in t["views"].items()
                if int(i) != game.source
                and isinstance(game, EvidenceGame)
                and game.known_capsules(v["history"])
            ]
            for key, view in t["views"].items():
                if (
                    int(key) != game.source
                    and not s.accurate
                    and any(
                        "id" in m
                        and isinstance(m.get("sender"), int)
                        and m.get("signal") == s.claim
                        for m in view["history"]
                    )
                ):
                    first_false_decision.setdefault(int(key), t["round"])
            for i in known:
                first_decision.setdefault(i, t["round"])
                first_action.setdefault(i, t["decisions"][str(i)]["action"])
                false_claims = [
                    m["id"]
                    for m in t["views"][str(i)]["history"]
                    if "id" in m
                    and isinstance(m.get("sender"), int)
                    and not s.accurate
                    and m.get("signal") == s.claim
                ]
                if false_claims and i not in first_joint:
                    first_joint[i] = t["round"]
                    first_joint_action[i] = t["decisions"][str(i)]["action"]
                    joint_ids[i] = false_claims
            result = await game.step(Replay())
            if isinstance(game, EvidenceGame):
                for i in range(10):
                    if i != game.source and game.known_capsules(
                        game.state.histories[i]
                    ):
                        initial_receipts.setdefault(i, t["round"])
            if canonical(result) != canonical(t):
                errors.append("transition_replay_mismatch")
            rounds.append(
                dict(
                    round=t["round"],
                    authenticated_before_decision=known,
                    evacuated_fraction=sum(
                        i in game.state.evacuated for i in range(10) if i != game.source
                    )
                    / 9,
                )
            )
        if m["status"] == "completed":
            outcome = json.loads((folder / "outcome.json").read_text())
            if canonical(outcome) != canonical(game.outcomes()):
                errors.append("outcome_replay_mismatch")
            if not (
                len(metadata) == len(responses) == m["decision_attempts"] == used
                and len(traces) == s.terminal_round
            ):
                errors.append("complete_call_or_round_mismatch")
        else:
            outcome = {}
    except Exception as exc:
        outcome = {}
        errors.append(f"{type(exc).__name__}: {exc}")
    return dict(
        **m,
        returned_provider_calls=len(metadata),
        cost_usd=sum(c["usage"]["cost"] for c in metadata),
        audit_errors=errors,
        evidence_timing=(
            [
                dict(
                    agent=i,
                    witness=i == game.witness,
                    first_receipt_round=initial_receipts.get(i),
                    first_active_authenticated_decision=first_decision.get(i),
                    first_active_false_peer_signal_decision=first_false_decision.get(i),
                    false_peer_signal_preceded_authenticated_decision=(
                        first_false_decision[i] < first_decision[i]
                        if i in first_false_decision and i in first_decision
                        else None
                    ),
                    action_at_first_authenticated_decision=first_action.get(i),
                    evacuation_round=game.state.evacuated.get(i),
                    first_active_decision_with_evidence_and_false_peer_signal=first_joint.get(
                        i
                    ),
                    action_at_first_joint_exposure=first_joint_action.get(i),
                    false_peer_signal_ids_at_joint_exposure=joint_ids.get(i, []),
                )
                for i in range(10)
                if i != game.source
            ]
            if isinstance(game, EvidenceGame)
            else []
        ),
        rounds=rounds,
        outcome=outcome,
    )


def contrasts(rows, section, baseline):
    pairs = []
    if section == "terra":
        base = {
            (r["scenario"], r["language"]): r
            for r in baseline
            if r["seed"] == 1000 and r["status"] == "completed"
        }
        for r in rows:
            b = base.get((r["scenario"]["id"], r["language"]))
            if r["status"] == "completed" and b:
                pairs.append(
                    dict(
                        scenario=r["scenario"]["id"],
                        language=r["language"],
                        difference=r["outcome"]["correct_action_rate"]
                        - b["correct_action_rate"],
                    )
                )
    else:
        control = "none" if section == "4" else "private_text"
        treat = "broadcast" if section == "4" else "private_proof"
        controls = {
            (r["model_tag"], r["scenario"]["id"]): r
            for r in rows
            if r["arm"] == control and r["status"] == "completed"
        }
        for r in rows:
            b = controls.get((r["model_tag"], r["scenario"]["id"]))
            if r["arm"] == treat and r["status"] == "completed" and b:
                metric = (
                    "correct_action_rate"
                    if section == "4"
                    else "other_recipients_correct_action_rate"
                )
                pairs.append(
                    dict(
                        model_tag=r["model_tag"],
                        scenario=r["scenario"]["id"],
                        disaster=r["scenario"]["disaster"],
                        difference=r["outcome"][metric] - b["outcome"][metric],
                    )
                )
    return pairs


def plots(rows, section, baseline, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharey=True)
    if section == "terra":
        groups = ["Sonnet EN", "Sonnet VI", "Terra EN", "Terra VI"]
        for ax, (disaster, accurate) in zip(
            axes.flat, [(False, False), (False, True), (True, False), (True, True)]
        ):
            ys = []
            for model, lang in [
                ("sonnet", "en"),
                ("sonnet", "vi"),
                ("terra", "en"),
                ("terra", "vi"),
            ]:
                rs = (
                    [
                        r
                        for r in baseline
                        if r["seed"] == 1000
                        and r["language"] == lang
                        and r["disaster"] == disaster
                        and r["accurate"] == accurate
                        and r["status"] == "completed"
                    ]
                    if model == "sonnet"
                    else [
                        r
                        for r in rows
                        if r["language"] == lang
                        and r["scenario"]["disaster"] == disaster
                        and r["scenario"]["accurate"] == accurate
                        and r["status"] == "completed"
                    ]
                )
                vals = [
                    r["correct_action_rate"]
                    if model == "sonnet"
                    else r["outcome"]["correct_action_rate"]
                    for r in rs
                ]
                ax.text(len(ys), 1.06, f"n={len(vals)}", ha="center")
                ys.append(mean(vals) if vals else float("nan"))
            ax.bar(range(4), ys, color=["#688fba", "#9cb9d8", "#d58e38", "#e8b97d"])
            ax.set_xticks(range(4), groups, rotation=20)
            ax.set_title(
                f"{'Disaster' if disaster else 'No disaster'} / "
                f"{'correct' if accurate else 'false'} claim"
            )
    else:
        groups = (
            ["none", "broadcast"]
            if section == "4"
            else ["private_text", "private_proof"]
        )
        metric = (
            "correct_action_rate"
            if section == "4"
            else "other_recipients_correct_action_rate"
        )
        for ax, (model, disaster) in zip(
            axes.flat,
            [("sonnet", False), ("sonnet", True), ("terra", False), ("terra", True)],
        ):
            for i, arm in enumerate(groups):
                vals = [
                    r["outcome"][metric]
                    for r in rows
                    if r["model_tag"] == model
                    and r["scenario"]["disaster"] == disaster
                    and r["arm"] == arm
                    and r["status"] == "completed"
                ]
                if vals:
                    ax.bar(i, mean(vals), width=0.65, color="#245ca6", alpha=0.65)
                    ax.scatter(
                        i + np.linspace(-0.1, 0.1, len(vals)), vals, color="#162a43"
                    )
                ax.text(i, 1.06, f"n={len(vals)}", ha="center")
            ax.set_xticks(range(2), [a.replace("_", " ") for a in groups])
            ax.set_title(
                f"{model.title()} / "
                f"{'disaster' if disaster else 'no disaster'} / false source claim"
            )
    for ax in axes.flat:
        ax.set_ylim(-0.03, 1.15)
        ax.set_ylabel(
            "Fraction correct" if section != "5" else "Non-witness fraction correct"
        )
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle(
        "Terra matched served-model check"
        if section == "terra"
        else f"Experiment {section} · evidence diagnostics"
    )
    note = (
        (
            "Broadcast evidence precedes round 1 peer messages; "
            "tiny exploratory sample; no general safety claim."
        )
        if section == "4"
        else (
            "Automatic transport bundles truth and provenance; tiny sample; "
            "no pure provenance-effect claim."
        )
        if section == "5"
        else (
            "Whole games; tiny exploratory sample; model and host differ; "
            "no significance or general safety claim."
        )
    )
    fig.text(
        0.5,
        0.01,
        note,
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=[0, 0.035, 1, 0.95])
    fig.savefig(output / "outcomes.png", dpi=170)
    plt.close(fig)

    dynamic_rows = rows
    if section == "terra":
        dynamic_rows = [
            dict(
                r,
                arm=(
                    "Danger claim"
                    if r["scenario"]["disaster"] == r["scenario"]["accurate"]
                    else "Safe claim"
                ),
            )
            for r in rows
        ]
        dynamic_rows += [
            dict(
                model_tag="sonnet",
                status=r["status"],
                rounds=r["rounds"],
                scenario={"disaster": r["disaster"]},
                arm=(
                    "Danger claim" if r["disaster"] == r["accurate"] else "Safe claim"
                ),
            )
            for r in baseline
            if r["seed"] == 1000
        ]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for model, ax in zip(["sonnet", "terra"], axes):
        arms = sorted({r["arm"] for r in dynamic_rows if r["model_tag"] == model})
        for arm in arms:
            rs = [
                r
                for r in dynamic_rows
                if r["model_tag"] == model
                and r["arm"] == arm
                and r["scenario"]["disaster"]
                and r["status"] == "completed"
            ]
            xs = sorted({t["round"] for r in rs for t in r["rounds"]})
            if xs:
                ys = [
                    mean(
                        t["evacuated_fraction"]
                        for r in rs
                        for t in r["rounds"]
                        if t["round"] == x
                    )
                    for x in xs
                ]
                ax.plot(xs, ys, marker="o", label=arm.replace("_", " "))
        ax.set_title(model.title() + " / disaster games")
        ax.set_ylim(-0.03, 1.03)
        ax.set_xlabel("Round")
        ax.grid(alpha=0.2)
        if arms:
            ax.legend(fontsize=8)
    axes[0].set_ylabel("Cumulative recipient evacuation fraction")
    fig.suptitle("Observed action timing; active game counts vary by terminal round")
    fig.tight_layout()
    fig.savefig(output / "dynamics.png", dpi=170)
    plt.close(fig)


def timing_plot(rows, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharey=True)
    measures = [
        "authenticated receipt",
        "active authenticated decision",
        "correct action",
    ]
    for ax, (model, disaster) in zip(
        axes.flat,
        [("sonnet", False), ("sonnet", True), ("terra", False), ("terra", True)],
    ):
        for a, arm in enumerate(["private_text", "private_proof"]):
            rs = [
                r
                for r in rows
                if r["status"] == "completed"
                and r["model_tag"] == model
                and r["scenario"]["disaster"] == disaster
                and r["arm"] == arm
            ]
            values = []
            if rs:
                received = [
                    sum(
                        t["first_receipt_round"] is not None
                        for t in r["evidence_timing"]
                        if not t["witness"]
                    )
                    / 8
                    for r in rs
                ]
                active = [
                    sum(
                        t["first_active_authenticated_decision"] is not None
                        for t in r["evidence_timing"]
                        if not t["witness"]
                    )
                    / 8
                    for r in rs
                ]
                correct = [
                    r["outcome"]["other_recipients_correct_action_rate"] for r in rs
                ]
                values = [mean(received), mean(active), mean(correct)]
            for j, (value, label, color) in enumerate(
                zip(values, measures, ["#b6cce2", "#527eaa", "#d58e38"])
            ):
                ax.bar(
                    a + (j - 1) * 0.23,
                    value,
                    width=0.22,
                    color=color,
                    label=label if a == 0 else None,
                )
            ax.text(a, 1.06, f"n={len(rs)}", ha="center")
        ax.set_xticks([0, 1], ["text only", "proof preserving"])
        ax.set_ylim(-0.02, 1.15)
        ax.grid(axis="y", alpha=0.2)
        ax.set_title(f"{model.title()} / {'disaster' if disaster else 'no disaster'}")
        ax.set_ylabel("Mean whole-game non-witness fraction")
    axes[0, 0].legend(fontsize=8, loc="lower right")
    fig.suptitle("Authenticated receipt, decision opportunity and final correctness")
    fig.text(
        0.5,
        0.015,
        (
            "Ordinary testimony is separate from authenticated receipt; "
            "correctness does not establish belief."
        ),
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=[0, 0.04, 1, 0.95])
    fig.savefig(output / "timing.png", dpi=170)
    plt.close(fig)


async def main(args):
    root, section = args.root, args.section
    output = Path("reports/overnight-experiments") / (
        "terra-comparison" if section == "terra" else f"experiment-{section}"
    )
    output.mkdir(exist_ok=True, parents=True)
    plan = json.loads((root / "plan.json").read_text())
    errors = []
    for path, expected in plan["source_sha256"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            errors.append("frozen_source_changed:" + path)
    if (
        hashlib.sha256(Path("data/experiment1/languages.json").read_bytes()).hexdigest()
        != plan["packs_sha256"]
    ):
        errors.append("pack_changed")
    packs = json.loads(Path("data/experiment1/languages.json").read_text())
    allrows = []
    folders = sorted(root.glob("*/manifest.json"))
    for p in folders:
        m = json.loads(p.read_text())
        if ORDER[m["section"]] <= ORDER[section]:
            allrows.append(await audit(p.parent, packs, plan["models"]))
    rows = [r for r in allrows if r["section"] == section]
    expected = {j["id"] for j in plan["jobs"] if j["section"] == section}
    if expected != {r["id"] for r in rows}:
        errors.append("unattempted_planned_games")
    errors += [
        dict(id=r["id"], errors=r["audit_errors"]) for r in allrows if r["audit_errors"]
    ]
    sections = {j["id"]: j["section"] for j in plan["jobs"]}
    spent, pending, max_exposure = 0.0, {}, 0.0
    for e in load(root / "budget.jsonl"):
        if e["type"] not in {"reserve", "settle"}:
            continue
        if ORDER[sections[e["ticket"].rsplit(":", 1)[0]]] > ORDER[section]:
            continue
        if e["type"] == "reserve":
            pending[e["ticket"]] = e["usd"]
        else:
            pending.pop(e["ticket"])
            spent += e["cost"]
        max_exposure = max(max_exposure, spent + sum(pending.values()))
    if pending or max_exposure > plan["extension_cap_usd"]:
        errors.append("budget_pending_or_exceeded")
    if abs(spent - sum(r["cost_usd"] for r in allrows)) > 1e-8:
        errors.append("cost_ledger_mismatch")
    baseline = json.loads(
        Path("reports/overnight-experiments/experiment-1/summary.json").read_text()
    )["games"]
    pairs = contrasts(rows, section, baseline)
    positive_controls = []
    if section == "4":
        for model in plan["models"]:
            for seed in (1000, 1001):
                for disaster in (False, True):
                    cell = next(
                        (
                            r
                            for r in rows
                            if r["model_tag"] == model
                            and r["scenario"]["seed"] == seed
                            and r["scenario"]["disaster"] == disaster
                            and r["arm"] == "broadcast"
                        ),
                        None,
                    )
                    status = cell["status"] if cell else "not_attempted"
                    passed = (
                        (
                            cell["outcome"]["missed_evacuation_rate"] <= 1 / 9
                            if disaster
                            else cell["outcome"]["unnecessary_evacuation_rate"] <= 1 / 9
                        )
                        if status == "completed"
                        else None
                    )
                    positive_controls.append(
                        dict(
                            model=model,
                            seed=seed,
                            disaster=disaster,
                            status=status,
                            passed=passed,
                            observed_evacuation_rate=(
                                (1 - cell["outcome"]["missed_evacuation_rate"])
                                if disaster
                                else cell["outcome"]["unnecessary_evacuation_rate"]
                            )
                            if status == "completed"
                            else None,
                            criterion=">=8/9 evacuate"
                            if disaster
                            else "<=1/9 evacuate",
                        )
                    )
    summary = dict(
        section=section,
        planned=len(expected),
        statuses=dict(Counter(r["status"] for r in rows)),
        decision_attempts=sum(r["decision_attempts"] for r in rows),
        returned_provider_calls=sum(r["returned_provider_calls"] for r in rows),
        section_cost_usd=sum(r["cost_usd"] for r in rows),
        extension_cumulative_usd=spent,
        original_cost_usd=plan["original_reported_usd"],
        total_cost_usd=spent + plan["original_reported_usd"],
        pending_reservations=len(pending),
        max_accounted_total_usd=max_exposure + plan["original_reported_usd"],
        audit_errors=errors,
        positive_controls=positive_controls,
        positive_control_established=(
            all(c["passed"] is True for c in positive_controls)
            if positive_controls
            else None
        ),
        paired_contrasts=pairs,
        games=rows,
        analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )
    (output / "plan.json").write_text(json.dumps(plan, indent=2))
    with (output / "games.csv").open("w") as f:
        fields = [
            "id",
            "status",
            "model",
            "language",
            "arm",
            "scenario",
            "disaster",
            "correct_action_rate",
            "other_recipients_correct_action_rate",
            "witness_correct",
            "authenticated_recipients",
            "decision_attempts",
            "returned_provider_calls",
            "cost_usd",
            "error",
        ]
        writer = csv.DictWriter(
            f, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                dict(
                    **{k: v for k, v in r.items() if k not in {"scenario", "model"}},
                    model=r["model_tag"],
                    scenario=r["scenario"]["id"],
                    disaster=r["scenario"]["disaster"],
                    **r["outcome"],
                )
            )
    with gzip.open(output / "raw-records.jsonl.gz", "wt", encoding="utf-8") as archive:
        for p in folders:
            if json.loads(p.read_text())["section"] != section:
                continue
            for file in sorted(p.parent.iterdir()):
                archive.write(
                    json.dumps(
                        dict(
                            path=str(file.relative_to(root)), content=file.read_text()
                        ),
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        archive.write(
            json.dumps(
                dict(path="budget.jsonl", content=(root / "budget.jsonl").read_text())
            )
            + "\n"
        )
    plots(rows, section, baseline, output)
    if section == "5":
        timing_plot(rows, output)
    print(
        json.dumps(
            {
                k: v
                for k, v in summary.items()
                if k not in {"games", "paired_contrasts"}
            },
            indent=2,
        )
    )
    if errors:
        raise SystemExit("Audit errors; interpretation blocked")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("runs/evidence-diagnostics-v2"))
    p.add_argument("--section", choices=["terra", "4", "5"], required=True)
    asyncio.run(main(p.parse_args()))
