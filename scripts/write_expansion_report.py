"""Write a plain-language expansion report and Matplotlib charts from audited data."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/oversight-expansion-v2"
OUT = ROOT / "submission/expansion-v2"


def write_report(folder=RUN, output=OUT):
    m = json.loads((folder / "metrics.json").read_text())
    spec = json.loads((folder / "FROZEN_PROTOCOL.json").read_text())["spec"]
    rows = [
        json.loads(line) for line in (folder / "trials.jsonl").read_text().splitlines()
    ]
    assert m["recorded_calls"] == len(rows) == 600 and m["pending"] == 0
    output.mkdir(parents=True, exist_ok=True)
    groups = {(r["evidence"], r["arm"]): r for r in m["live_groups"]}
    a = groups["absent", "normalized_structural"]
    b = groups["absent", "normalized_semantic"]
    c = groups["present", "normalized_structural"]
    d = groups["present", "normalized_semantic"]
    contrasts = {r["evidence"]: r for r in m["paired_task_contrasts"]}
    lines = [
        "# Expanded study of multilingual agent handoffs",
        "",
        "**Track 4: Multi-Agent Oversight and Control**",
        "",
        "## What changed",
        "",
        "This is a separate, prospectively frozen expansion of the original pilot. "
        "The pilot remains unchanged: 24 responses from two task groups. "
        "The expansion assigns 600 worker responses across 50 previously unused "
        "task IDs, with 200 responses per message language. These are different "
        "synthetic topics and fact values within one fixed reporting task, "
        "not 50 independent task families.",
        "",
        "## Research questions and hypotheses",
        "",
        "**RQ1:** Without trusted facts in the worker input, does a fact check "
        "block wrong budgets that a structural check releases? **H1:** It will "
        "reduce wrong releases without adding rejection of correct reports.",
        "",
        "**RQ2:** Does the fact check add protection when the worker already "
        "receives trusted facts? **H2:** It will reduce wrong releases beyond "
        "trusted input and structural checking alone. If the grounded baseline "
        "has no observed errors, an additional benefit cannot be demonstrated.",
        "",
        "**Exploratory RQ3:** Does the same pattern appear in English, Vietnamese "
        "and Chinese review notes? We report counts, not a causal language effect. "
        "These hypotheses were frozen locally before the expansion's model calls; "
        "this is not an external preregistration.",
        "",
        "## Method",
        "",
        "The design is 50 tasks × 3 languages × 2 source conditions "
        "(clean or deliberately wrong budget) × 2 worker-information conditions "
        "(trusted record absent or present). This gives 600 responses. Each task "
        "contributes twelve responses and each language contributes 200.",
        "",
        "We exclude task IDs appearing in previous saved experiment inputs and "
        "the earlier selected 500/600-case files. Selection and request order "
        "use fixed seeds. Budgets, risk levels and deadlines vary across tasks. "
        "The English task description is visible in both evidence conditions. "
        "Peer-source messages are deterministic templates, not new model outputs. "
        "The review note varies by language, while JSON keys, fact labels and "
        "task descriptions remain English. This is a mixed-language experiment; "
        "translations have not received bilingual human review.",
        "",
        f"The worker is `{spec['model']}` through Adaption at temperature 0.7 "
        "with a 4096-token output cap. Tools, memory and persistent response "
        "storage are disabled. Both evidence conditions have the same system "
        "prompt and user payload except the trusted-record field. All 300 "
        "prompt pairs are audited. The single-pass stop rule is 600 assigned "
        "requests; transport retries on HTTP 429 are bounded and logged.",
        "",
        "Every raw response is evaluated by four paired checks: strict or "
        "shared JSON parsing crossed with structural or trusted-fact checking. "
        "Both controller arms receive the same record. Accepted objects remain "
        "unchanged; there are no repair calls or trusted-output rewriting in "
        "this comparison. Correctness is scored independently of guard approval. "
        "The primary contrast uses shared normalization. The comparator still "
        "enforces structural rules; it is not a completely unconstrained agent.",
        "",
        "## Results",
        "",
        f"Recorded requests: **{m['recorded_calls']}/600**. Usable responses: "
        f"**{m['returned_calls']}**. Unscored errors: **{m['errors']}**. "
        f"Raw responses passing strict structural validation: "
        f"**{m['raw_strict_structural_valid']}/{m['returned_calls']}**.",
        "",
        "| Worker trusted input | Check | Assigned | Wrong/missing budget released | "
        "Correct released | Blocked | Correct blocked | Errors |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for evidence in ("absent", "present"):
        for arm, label in (
            ("normalized_structural", "Structural"),
            ("normalized_semantic", "Plus fact check"),
        ):
            g = groups[evidence, arm]
            lines.append(
                f"| {evidence} | {label} | {g['assigned']} | "
                f"{g['wrong_budget_releases']} | {g['correct_releases']} | "
                f"{g['blocked_candidates']} | {g['blocked_correct_candidates']} | "
                f"{g['unscored_errors']} |"
            )
    lines += [
        "",
        "![Release decisions](outcome-bars.png)",
        "",
        "*Figure 1. Correct releases, incorrect releases, blocks and unscored "
        "errors are separate. The two bars in an evidence condition reuse "
        "the same 300 responses. Blocked reports are not repaired tasks.*",
        "",
        f"For RQ1, wrong-budget releases change from {a['wrong_budget_releases']} "
        f"to {b['wrong_budget_releases']}. Correct releases change from "
        f"{a['correct_releases']} to {b['correct_releases']}, with "
        f"{b['blocked_correct_candidates']} correct candidates blocked "
        "by the fact check. "
        "Interpret H1 from both error reduction and preservation of correct reports, "
        "rather than from the number of rejections alone.",
        "",
        f"For RQ2, the grounded worker produces "
        f"{c['wrong_budget_releases']} wrong-budget releases under structural "
        f"checking and {d['wrong_budget_releases']} with the added fact check. "
        + (
            "No additional protection beyond grounding is observed in this run. "
            "This is not evidence that grounding always suffices."
            if c["wrong_budget_releases"] == d["wrong_budget_releases"] == 0
            else "Report the observed paired difference, rather than assuming "
            "that an added guard necessarily helps."
        ),
        "",
        "![Language counts](language-heatmap.png)",
        "",
        "*Figure 2. Wrong/missing budgets released per language, with assigned "
        "denominators shown. Each language repeats the same 50 tasks. Unscored "
        "errors, if present, are listed in the table and metrics; zero observed "
        "wrong releases does not make those errors safe.*",
        "",
        "## Paired task-level analysis",
        "",
        "The uncertainty calculation resamples whole task clusters, keeping "
        "the six response conditions within an evidence arm together. It uses "
        "5,000 bootstrap draws with a fixed seed. Tasks missing any required "
        "response in that evidence arm are excluded from the complete-case "
        "interval and counted explicitly. Error bounds over assigned cases "
        "are retained separately in the metrics.",
        "",
    ]
    for evidence in ("absent", "present"):
        p = contrasts[evidence]
        effect = p["structural_minus_semantic_rate"]
        interval = p["task_cluster_bootstrap_95_percentile_interval"]
        lines.append(
            f"- **{evidence}:** {p['complete_task_clusters']} complete task "
            f"clusters; {p['excluded_incomplete_clusters']} incomplete clusters "
            f"excluded. Structural minus semantic wrong-budget release rate: "
            f"{effect}. Task-bootstrap 95% percentile interval: {interval}."
        )
    lines += [
        "",
        "A zero-width interval can occur when every selected task has the same "
        "measured difference. It describes this set of synthetic reporting "
        "tasks; it is not a precise bound on real-world attack risk or proof "
        "of general safety. Language variants are not independent new tasks.",
        "",
        "## Actual sample inputs and outputs",
        "",
        "The following examples are selected deterministically from the first "
        "frozen task cluster, English, in clean-absent, poisoned-absent and "
        "poisoned-present order. They are saved model responses, not generated "
        "illustrations. Complete parsed inputs/outputs and decisions for all "
        "600 cases are supplied in `recorded-outputs.json` and `recorded-outputs.csv`.",
    ]
    exported = []
    for row in rows:
        record = {
            k: row[k]
            for k in (
                "trial_id",
                "task_cluster",
                "language",
                "kind",
                "evidence",
                "expected",
                "completed",
            )
        }
        record["peer_report"] = json.loads(
            json.loads(row["messages"][1]["content"])["peer_report"]
        )
        record["task_description"] = row["task"]["topic"]
        if row["completed"]:
            record["raw_worker_output"] = row["response"]["content"]
            record["extracted_facts"] = row["oracle"]["extracted_facts"]
            for arm in ("normalized_structural", "normalized_semantic"):
                record[arm] = {
                    k: row["checks"][arm][k]
                    for k in ("allowed", "reasons", "released_object")
                }
        else:
            record["error"] = row.get("error")
        exported.append(record)
    (output / "recorded-outputs.json").write_text(
        json.dumps(exported, ensure_ascii=False, indent=2) + "\n"
    )
    fields = (
        "trial_id",
        "task_cluster",
        "language",
        "kind",
        "evidence",
        "completed",
        "expected_budget",
        "worker_budget",
        "structural_allowed",
        "semantic_allowed",
        "raw_worker_output",
    )
    with (output / "recorded-outputs.csv").open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for record in exported:
            flat = {k: record[k] for k in fields if k in record}
            flat["expected_budget"] = record["expected"]["budget"]
            flat["worker_budget"] = record.get("extracted_facts", {}).get("budget")
            flat["structural_allowed"] = record.get("normalized_structural", {}).get(
                "allowed"
            )
            flat["semantic_allowed"] = record.get("normalized_semantic", {}).get(
                "allowed"
            )
            writer.writerow(flat)
    for kind, evidence in (
        ("clean", "absent"),
        ("poisoned", "absent"),
        ("poisoned", "present"),
    ):
        example = next(
            r
            for r in exported
            if r["task_cluster"] == 0
            and r["language"] == "en"
            and r["kind"] == kind
            and r["evidence"] == evidence
        )
        lines += [
            "",
            f"### {kind}, trusted input {evidence}",
            "",
            f"Trial: `{example['trial_id']}`. Expected facts: "
            f"`{json.dumps(example['expected'])}`.",
            "",
            "Peer input:",
            "```json",
            json.dumps(example["peer_report"], ensure_ascii=False, indent=2),
            "```",
            "",
            "Exact worker output:",
            "```json",
            example.get("raw_worker_output", "No usable response; unscored error"),
            "```",
        ]
        if example["completed"]:
            lines.append(
                "Decisions: "
                + "; ".join(
                    f"{arm}: {example[arm]['allowed']}, "
                    f"reasons={example[arm]['reasons']}"
                    for arm in ("normalized_structural", "normalized_semantic")
                )
            )
    lines += [
        "",
        "## Limits and conclusion",
        "",
        "The expansion provides more task IDs and fact values than the pilot, "
        "but the guard still checks known fields in a single reporting contract. "
        "Its access to a correct controller record is assumed. The templates "
        "deliberately insert wrong budgets; copying them without independent "
        "evidence is not a general jailbreak result. Full multilingual prompts, "
        "human translation review, new task families, multiple model families "
        "and live distributed swarms remain untested. No success claim should "
        "combine blocked reports with correctly completed tasks.",
        "",
        "## Dataset and reproduction",
        "",
        "- [Frozen protocol](../../runs/oversight-expansion-v2/FROZEN_PROTOCOL.json)",
        "- [600 exact input prompts](../../runs/oversight-expansion-v2/inputs.jsonl)",
        "- [Raw provider responses and decisions]"
        "(../../runs/oversight-expansion-v2/trials.jsonl)",
        "- [Audited metrics](../../runs/oversight-expansion-v2/metrics.json)",
        "- [Readable JSON outputs](recorded-outputs.json)",
        "- [Readable CSV outputs](recorded-outputs.csv)",
        "",
        "```sh",
        "uv run python scripts/report_oversight_expansion.py",
        "python scripts/write_expansion_report.py",
        "```",
        "",
        "The report writer requires the existing figure requirements (Matplotlib). "
        "It performs no inference. Earlier run files are checked against their "
        f"frozen hashes: **{m['prior_run_files_verified_unchanged']} "
        "files unchanged**. "
        f"Provider-reported cost fields sum to **{m['provider_reported_cost']:.6f}**, "
        f"available for {m['responses_with_reported_cost']} usable responses. "
        "This is provider-reported accounting, not a separately verified invoice.",
    ]
    lines += [
        "",
        "## Separate proposed budget committee extension",
        "",
        "The [budget swarm design](../../research/BUDGET_SWARM_EXTENSION.md) "
        "introduces private evidence, multi-round deliberation, final votes "
        "and an optional contingent simulated offer with accept/decline choices. "
        "It is a design specification, not an executed bribery or swarm study. "
        "The present reporting results and the earlier pilot remain separate.",
        "",
        "The [expanded Word report](Track4_Expanded_600.docx) retains the "
        "supplied template and APA 7 references. Author details remain pending.",
    ]
    (output / "README.md").write_text("\n".join(lines) + "\n")
    provenance = {
        "metrics_sha256": hashlib.sha256(
            (folder / "metrics.json").read_bytes()
        ).hexdigest(),
        "trials_sha256": hashlib.sha256(
            (folder / "trials.jsonl").read_bytes()
        ).hexdigest(),
        "note": (
            "Expansion only; pilot remains separate. "
            "Charts use counts from the audited metrics."
        ),
    }
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    draw_charts(m, output)
    for svg in output.glob("*.svg"):
        svg.write_text(
            "\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n"
        )
    print(output / "README.md")


def draw_charts(metrics, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import Patch

    plt.rcParams.update(
        {"font.family": "DejaVu Sans", "font.size": 11, "svg.fonttype": "none"}
    )
    fig, axs = plt.subplots(2, 1, figsize=(9.4, 4.7), sharex=True)
    colors = {
        "correct": "#39749C",
        "wrong": "#D38633",
        "blocked": "#B7BEC6",
        "errors": "#EEEEEE",
    }
    groups = {(r["evidence"], r["arm"]): r for r in metrics["live_groups"]}
    for i, evidence in enumerate(("absent", "present")):
        ax = axs[i]
        for y, arm in zip([1, 0], ["normalized_structural", "normalized_semantic"]):
            g = groups[evidence, arm]
            parts = [
                ("correct", g["correct_releases"]),
                ("wrong", g["wrong_budget_releases"] + g["other_incorrect_releases"]),
                ("blocked", g["blocked_candidates"]),
                ("errors", g["unscored_errors"]),
            ]
            assert sum(n for _, n in parts) == g["assigned"]
            left = 0
            for kind, count in parts:
                if count:
                    ax.barh(
                        y,
                        count,
                        left=left,
                        height=0.56,
                        color=colors[kind],
                        edgecolor="#333333",
                        linewidth=0.5,
                    )
                    ax.text(
                        left + count / 2,
                        y,
                        str(count),
                        ha="center",
                        va="center",
                        fontsize=11,
                        color="white" if kind == "correct" else "#111111",
                    )
                left += count
        ax.set_yticks([1, 0], ["Structural", "Plus fact check"])
        ax.set_title(
            "Worker trusted input " + evidence,
            loc="left",
            fontweight="bold",
            fontsize=12,
        )
        ax.set_ylim(-0.6, 1.6)
        ax.spines[["top", "right", "left"]].set_visible(False)
    axs[1].set_xlim(0, 300)
    axs[1].set_xticks([0, 50, 100, 150, 200, 250, 300])
    axs[1].set_xlabel("Responses per check (same 300 responses per condition)")
    labels = ["Correct released", "Incorrect released", "Blocked", "Unscored error"]
    fig.legend(
        handles=[
            Patch(facecolor=c, label=label) for c, label in zip(colors.values(), labels)
        ],
        loc="upper center",
        ncol=4,
        fontsize=9,
        frameon=False,
    )
    fig.subplots_adjust(left=0.2, right=0.98, top=0.83, bottom=0.13, hspace=0.55)
    for ext in ["png", "svg"]:
        fig.savefig(output / f"outcome-bars.{ext}", dpi=300)
    plt.close(fig)
    cells = []
    labels = []
    for language in ["en", "vi", "zh"]:
        groups = {
            (r["evidence"], r["arm"]): r for r in metrics["language_groups"][language]
        }
        group = [
            groups[e, a]
            for e in ("absent", "present")
            for a in ("normalized_structural", "normalized_semantic")
        ]
        cells.append([r["wrong_budget_releases"] / r["assigned"] for r in group])
        labels.append(
            [f"{r['wrong_budget_releases']} / {r['assigned']}" for r in group]
        )
    fig, ax = plt.subplots(figsize=(9.2, 3.6))
    cmap = LinearSegmentedColormap.from_list("error_counts", ["#FFFDF2", "#D38633"])
    ax.imshow(cells, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for y in range(3):
        for x in range(4):
            ax.text(x, y, labels[y][x], ha="center", va="center", fontweight="bold")
    ax.set_xticks(
        range(4),
        [
            "No record\nStructural",
            "No record\nFact check",
            "Trusted record\nStructural",
            "Trusted record\nFact check",
        ],
    )
    ax.set_yticks(range(3), ["English", "Vietnamese", "Chinese"])
    ax.set_title(
        "Wrong/missing budgets released by review-note language", loc="left", pad=12
    )
    ax.tick_params(length=0, pad=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.subplots_adjust(left=0.17, right=0.98, top=0.83, bottom=0.24)
    for ext in ["png", "svg"]:
        fig.savefig(output / f"language-heatmap.{ext}", dpi=300)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=RUN)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    write_report(args.folder, args.output)


if __name__ == "__main__":
    main()
