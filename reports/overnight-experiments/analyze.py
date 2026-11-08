"""Replay saved transitions, audit raw responses and create descriptive game plots."""

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
from swarm_lab.evacuation.language import LanguageGame


def load(path):
    return (
        [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    )


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


async def audit_game(folder, packs):
    manifest = json.loads((folder / "manifest.json").read_text())
    traces = load(folder / "traces.jsonl")
    calls = load(folder / "calls.jsonl")
    errors = []
    metadata = [c for c in calls if c["type"] == "provider_metadata"]
    responses = [c for c in calls if c["type"] == "model_response"]
    for c in metadata:
        if (
            c["upstream_provider"] != "Google"
            or c["requested_reasoning_effort"] != "low"
            or c["model"] != "anthropic/claude-sonnet-5.5"
            or c["finish_reason"] != "stop"
        ):
            errors.append("provider_generation_mismatch")
    if manifest["status"] == "completed" and not (
        len(metadata) == len(responses) == manifest["calls"]
    ):
        errors.append("call_count_mismatch")
    scenario = Scenario(**manifest["scenario"])
    game = LanguageGame(
        scenario,
        manifest["language"],
        packs[manifest["language"]],
        identity=manifest["identity"],
        topology=manifest["topology"],
    )
    used = 0

    class Replay:
        async def decide(self, view):
            nonlocal used
            response = responses[used]
            used += 1
            if canonical(response["view"]) != canonical(view):
                raise ValueError("saved_response_view_mismatch")
            raw = response["raw"].strip()
            if raw.startswith("```json\n") and raw.endswith("\n```"):
                raw = raw[8:-4].strip()
            return json.loads(raw)

    rounds = []
    try:
        for trace in traces:
            replay = await game.step(Replay())
            if canonical(replay) != canonical(trace):
                errors.append("replay_transition_mismatch")
            messages = trace["messages"]
            active = [m for k, m in messages.items() if int(k) != game.source]
            rounds.append(
                dict(
                    round=trace["round"],
                    active=len(active),
                    claim_signal_rate=mean(
                        m["signal"] == scenario.claim for m in active
                    )
                    if active
                    else None,
                    evacuated_fraction=sum(
                        i in game.state.evacuated for i in range(10) if i != game.source
                    )
                    / 9,
                    direct_exposure_fraction=sum(
                        any(
                            m.get("sender") == game.source and "id" in m
                            for m in history
                        )
                        for i, history in game.state.histories.items()
                        if i != game.source
                    )
                    / 9,
                )
            )
        if manifest["status"] == "completed":
            outcome = json.loads((folder / "outcome.json").read_text())
            if canonical(outcome) != canonical(game.outcomes()):
                errors.append("outcome_replay_mismatch")
            if len(traces) != scenario.terminal_round or used != len(responses):
                errors.append("incomplete_round_or_response_accounting")
        else:
            outcome = {}
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
        outcome = {}
    row = dict(
        id=manifest["id"],
        section=manifest["section"],
        scenario=scenario.id,
        seed=scenario.seed,
        source=scenario.informant,
        disaster=scenario.disaster,
        accurate=scenario.accurate,
        language=manifest["language"],
        identity=manifest["identity"],
        topology=manifest["topology"],
        status=manifest["status"],
        calls=manifest["calls"],
        cost_usd=sum(c["usage"]["cost"] for c in metadata),
        error=manifest.get("error"),
        audit_errors=errors,
        rounds=rounds,
    )
    row.update(
        {
            k: outcome.get(k)
            for k in (
                "correct_action_rate",
                "missed_evacuation_rate",
                "unnecessary_evacuation_rate",
                "recipient_payoff",
                "evacuation_rounds",
                "adjacency",
            )
        }
    )
    return row


def contrasts(rows, section):
    base = {
        (r["scenario"], r["language"]): r
        for r in rows
        if r["section"] == 1 and r["status"] == "completed"
    }
    pairs = []
    if section == 1:
        en = {
            r["scenario"]: r
            for r in rows
            if r["section"] == 1
            and r["language"] == "en"
            and r["status"] == "completed"
        }
        for r in rows:
            if (
                r["section"] == 1
                and r["language"] == "vi"
                and r["status"] == "completed"
                and r["scenario"] in en
            ):
                pairs.append(
                    dict(
                        scenario=r["scenario"],
                        contrast="Vietnamese - English",
                        difference=r["correct_action_rate"]
                        - en[r["scenario"]]["correct_action_rate"],
                    )
                )
    else:
        for r in rows:
            b = base.get((r["scenario"], r["language"]))
            if r["section"] == section and r["status"] == "completed" and b:
                pairs.append(
                    dict(
                        scenario=r["scenario"],
                        language=r["language"],
                        contrast=r["identity"] if section == 2 else "random - ring",
                        difference=r["correct_action_rate"] - b["correct_action_rate"],
                    )
                )
    return pairs


def plots(rows, section, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    selected = [
        r
        for r in rows
        if r["status"] == "completed"
        and (
            r["section"] == section
            or (
                section in (2, 3)
                and r["section"] == 1
                and (section == 3 or r["seed"] == 1000)
            )
        )
    ]
    groups = (
        ["en", "vi"]
        if section == 1
        else [
            "ordinary_peer",
            "emergency_expert",
            "government_official",
            "xi_jinping",
            "buddhist_monk",
            "christian_pastor",
        ]
        if section == 2
        else ["ring", "random_regular"]
    )
    field = "language" if section == 1 else "identity" if section == 2 else "topology"
    labels = {
        "en": "English",
        "vi": "Vietnamese",
        "ordinary_peer": "Peer",
        "emergency_expert": "Expert",
        "government_official": "Official",
        "xi_jinping": "Xi label",
        "buddhist_monk": "Monk",
        "christian_pastor": "Pastor",
        "ring": "Ring",
        "random_regular": "Random regular",
    }
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharey=True)
    for ax, (disaster, accurate) in zip(
        axes.flat, [(False, False), (False, True), (True, False), (True, True)]
    ):
        for n, group in enumerate(groups):
            rs = [
                r
                for r in selected
                if r[field] == group
                and r["disaster"] == disaster
                and r["accurate"] == accurate
            ]
            ys = [r["correct_action_rate"] for r in rs]
            if ys:
                ax.bar(n, mean(ys), color="#245ca6", alpha=0.65, width=0.65)
                ax.scatter(
                    n + np.linspace(-0.12, 0.12, len(ys)), ys, color="#162a43", s=28
                )
                ax.text(n, 1.07, f"n={len(ys)}", ha="center", fontsize=8)
        ax.set_title(
            f"{'Disaster' if disaster else 'No disaster'} / "
            f"{'correct' if accurate else 'false'} source claim"
        )
        ax.set_xticks(range(len(groups)), [labels[g] for g in groups], rotation=20)
        ax.set_ylim(-0.03, 1.18)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
        ax.grid(axis="y", alpha=0.2)
        ax.set_ylabel("Fraction taking correct action")
    fig.suptitle(f"Experiment {section} · observed whole-game outcomes", fontsize=15)
    fig.text(
        0.5,
        0.015,
        "Dots = games, bars = descriptive means; draft translations; "
        "one model; no significance claims.",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=[0, 0.04, 1, 0.95])
    fig.savefig(output / "outcomes.png", dpi=170)
    fig.savefig(output / "outcomes.svg")
    svg = output / "outcomes.svg"
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n"
    )
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for group in groups:
        rs = [r for r in selected if r[field] == group]
        xs = sorted({t["round"] for r in rs for t in r["rounds"]})
        for ax, metric in zip(axes, ["claim_signal_rate", "evacuated_fraction"]):
            points = [
                (
                    x,
                    [
                        t[metric]
                        for r in rs
                        for t in r["rounds"]
                        if t["round"] == x and t[metric] is not None
                    ],
                )
                for x in xs
            ]
            points = [(x, mean(vs)) for x, vs in points if vs]
            if points:
                ax.plot(*zip(*points), marker="o", label=labels[group])
            ax.set_ylim(-0.03, 1.03)
            ax.set_xlabel("Round (remaining active games vary by terminal round)")
            ax.grid(alpha=0.2)
    axes[0].set_title("Active recipient signals matching the source claim")
    axes[1].set_title("Cumulative fraction of recipients evacuated")
    axes[0].set_ylabel("Mean across games")
    axes[1].legend(fontsize=8)
    fig.suptitle("Signals and actions; matching a claim does not establish belief")
    fig.tight_layout()
    fig.savefig(output / "dynamics.png", dpi=170)
    plt.close(fig)


async def main(args):
    root, section = args.root, args.section
    output = Path("reports/overnight-experiments") / f"experiment-{section}"
    output.mkdir(parents=True, exist_ok=True)
    plan = json.loads((root / "plan.json").read_text())
    packs = json.loads(Path("data/experiment1/languages.json").read_text())
    errors = []
    for path, expected in plan["sources"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            errors.append(f"frozen_source_changed:{path}")
    if (
        hashlib.sha256(Path("data/experiment1/languages.json").read_bytes()).hexdigest()
        != plan["pack_sha256"]
    ):
        errors.append("frozen_pack_changed")
    folders = sorted(root.glob("*/manifest.json"))
    rows = []
    for p in folders:
        m = json.loads(p.read_text())
        if m["section"] <= section:
            rows.append(await audit_game(p.parent, packs))
    selected = [r for r in rows if r["section"] == section]
    errors += [
        dict(id=r["id"], errors=r["audit_errors"]) for r in rows if r["audit_errors"]
    ]
    planned = [j for j in plan["jobs"] if j["section"] == section]
    if set(j["id"] for j in planned) != set(r["id"] for r in selected):
        errors.append("planned_attempted_id_mismatch")
    pairs = contrasts(rows, section)
    summary = dict(
        section=section,
        purpose=plan["purpose"],
        planned=len(planned),
        statuses=dict(Counter(r["status"] for r in selected)),
        calls=sum(r["calls"] for r in selected),
        section_cost_usd=sum(r["cost_usd"] for r in selected),
        cumulative_cost_usd=sum(r["cost_usd"] for r in rows),
        audit_errors=errors,
        paired_contrasts=pairs,
        games=selected,
        caveats=plan["inference_limits"],
        language_review="pending_manual_review",
    )
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )
    (output / "plan.json").write_text(json.dumps(plan, indent=2))
    with (output / "games.csv").open("w") as f:
        fields = [
            "id",
            "status",
            "scenario",
            "seed",
            "language",
            "identity",
            "topology",
            "disaster",
            "accurate",
            "correct_action_rate",
            "missed_evacuation_rate",
            "unnecessary_evacuation_rate",
            "calls",
            "cost_usd",
        ]
        writer = csv.DictWriter(
            f, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(selected)
    # Raw simulated inputs/outputs only; no env files, credentials or personal data.
    with gzip.open(output / "raw-records.jsonl.gz", "wt", encoding="utf-8") as archive:
        for p in folders:
            m = json.loads(p.read_text())
            if m["section"] != section:
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
    plots(rows, section, output)
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
        raise SystemExit("Audit errors: interpretation is blocked")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("runs/overnight-v1"))
    p.add_argument("--section", type=int, choices=[1, 2, 3], required=True)
    asyncio.run(main(p.parse_args()))
