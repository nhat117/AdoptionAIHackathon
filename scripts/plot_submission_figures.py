"""Rebuild report figures from saved results, with no model calls.

Requires matplotlib==3.10.7. Run with --outdir to choose the output folder.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Patch, Rectangle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    m = json.loads(args.metrics.read_text())
    rows = [
        r
        for evidence in ["absent", "present"]
        for arm in ["normalized_structural", "normalized_semantic"]
        for r in m["live_groups"]
        if r["evidence"] == evidence and r["arm"] == arm
    ]
    assert len(rows) == 4 and m["returned_calls"] == 24 and m["errors"] == 0
    for r in rows:
        assert (
            r["correct_releases"]
            + r["target_budget_releases"]
            + r["blocked_candidates"]
            == r["assigned"]
            == 12
        )
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "savefig.facecolor": "white",
            "svg.fonttype": "none",
        }
    )
    fig, axs = plt.subplots(2, 1, figsize=(9.4, 4.7), sharex=True)
    series = [
        ("correct_releases", "Correct released", "#39749C", ""),
        ("target_budget_releases", "Wrong released", "#D38633", "///"),
        ("blocked_candidates", "Blocked", "#B7BEC6", ".."),
    ]
    for i, ax in enumerate(axs):
        for y, r in zip([1, 0], rows[i * 2 : i * 2 + 2]):
            left = 0
            for key, label, color, hatch in series:
                value = r[key]
                if value:
                    ax.barh(
                        y,
                        value,
                        left=left,
                        height=0.57,
                        color=color,
                        edgecolor="#333333",
                        linewidth=0.6,
                        hatch=hatch,
                    )
                    ax.text(
                        left + value / 2,
                        y,
                        str(value),
                        ha="center",
                        va="center",
                        fontsize=12,
                        fontweight="bold",
                        color="white" if key == "correct_releases" else "#181818",
                    )
                left += value
        ax.set_title(
            ["Worker has no trusted record", "Worker has the trusted record"][i],
            loc="left",
            fontweight="bold",
            pad=8,
        )
        ax.set_yticks([1, 0], ["Structural check", "Plus fact check"])
        ax.set_ylim(-0.6, 1.6)
        ax.set_xlim(0, 12)
        ax.set_xticks(range(0, 13, 2))
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#888888")
        ax.tick_params(axis="y", length=0, pad=9)
        ax.set_axisbelow(True)
        ax.grid(axis="x", color="#E6E6E6", linewidth=0.7)
    axs[1].set_xlabel("Responses per check (same 12 responses within each condition)")
    fig.legend(
        handles=[
            Patch(facecolor=color, edgecolor="#333333", hatch=hatch, label=label)
            for _, label, color, hatch in series
        ],
        loc="upper center",
        bbox_to_anchor=(0.59, 1.01),
        ncol=3,
        frameon=False,
        fontsize=10,
    )
    fig.subplots_adjust(left=0.22, right=0.98, top=0.85, bottom=0.13, hspace=0.6)
    for ext in ["png", "svg"]:
        fig.savefig(args.outdir / f"results-comparison.{ext}", dpi=300)
    plt.close(fig)
    # Engineering diagram, also drawn with Matplotlib rather than an image model.
    fig, ax = plt.subplots(figsize=(10, 3.15))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.15)
    ax.axis("off")
    boxes = [
        (0.05, 1.1, 1.8, 0.75, "One response\nsame raw text"),
        (2.2, 1.1, 1.8, 0.75, "Shared parsing\nstrict or one fence"),
        (4.6, 2.05, 2.2, 0.75, "Structure only\nidentity and format"),
        (4.6, 0.35, 2.2, 0.75, "Structure plus\ntrusted fact agreement"),
        (7.6, 2.05, 2.25, 0.75, "Original object\nor withhold"),
        (7.6, 0.35, 2.25, 0.75, "Original object\nor withhold"),
    ]
    for x, y, w, h, label in boxes:
        ax.add_patch(
            Rectangle((x, y), w, h, edgecolor="#333333", facecolor="white", linewidth=1)
        )
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=11)
    for start, end in [
        ((1.85, 1.475), (2.2, 1.475)),
        ((4, 1.475), (4.6, 2.425)),
        ((4, 1.475), (4.6, 0.725)),
        ((6.8, 2.425), (7.6, 2.425)),
        ((6.8, 0.725), (7.6, 0.725)),
    ]:
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=13,
                linewidth=1,
                color="#333333",
            )
        )
    ax.text(
        5,
        0.04,
        "Both checks have the registry. No repair or rewriting contributes.",
        ha="center",
        fontsize=10,
    )
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    for ext in ["png", "svg"]:
        fig.savefig(args.outdir / f"oversight-flow.{ext}", dpi=300)
    plt.close(fig)
    fields = [
        "evidence",
        "arm",
        "assigned",
        "correct_releases",
        "target_budget_releases",
        "blocked_candidates",
    ]
    with (args.outdir / "results-chart-data.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: r[k] for k in fields} for r in rows)
    provenance = {
        "source": "runs/oversight-ablation-v1/metrics.json",
        "sha256": hashlib.sha256(args.metrics.read_bytes()).hexdigest(),
        "renderer": "Matplotlib",
        "matplotlib_version": matplotlib.__version__,
        "rows": rows,
        "notes": (
            "24 unique responses. Paired checks reuse candidates. "
            "Blocked reports are not repaired. No new inference."
        ),
    }
    (args.outdir / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n"
    )
    extra_figures(args.metrics, args.outdir)
    print("Five figures rendered with Matplotlib", matplotlib.__version__)


def extra_figures(metrics_path, outdir):
    """Plot additional views of the same saved trials; never request new outputs."""
    trials_path = metrics_path.with_name("trials.jsonl")
    trials = [json.loads(line) for line in trials_path.read_text().splitlines()]
    metrics = json.loads(metrics_path.read_text())
    assert len(trials) == metrics["returned_calls"] == 24
    languages = ["en", "vi", "zh"]
    conditions = [
        ("absent", "normalized_structural"),
        ("absent", "normalized_semantic"),
        ("present", "normalized_structural"),
        ("present", "normalized_semantic"),
    ]
    cells, source_rows = [], []
    for language in languages:
        row = []
        for evidence, arm in conditions:
            subset = [
                r
                for r in trials
                if r["language"] == language and r["evidence"] == evidence
            ]
            assert len(subset) == 4
            wrong = sum(
                r["checks"][arm]["allowed"]
                and r["oracle"]["extracted_facts"]["budget"] != r["expected"]["budget"]
                for r in subset
            )
            row.append(wrong)
            source_rows.append(
                dict(
                    language=language,
                    evidence=evidence,
                    arm=arm,
                    wrong_releases=wrong,
                    responses=4,
                )
            )
        cells.append(row)
    fig, ax = plt.subplots(figsize=(9.2, 3.7))
    ax.imshow(cells, cmap="YlOrBr", vmin=0, vmax=4, aspect="auto")
    for y, row in enumerate(cells):
        for x, count in enumerate(row):
            ax.text(
                x,
                y,
                f"{count} / 4",
                ha="center",
                va="center",
                fontsize=13,
                fontweight="bold",
                color="#202020",
            )
    ax.set_xticks(
        range(4),
        [
            "No record\nStructure",
            "No record\nFact check",
            "Trusted record\nStructure",
            "Trusted record\nFact check",
        ],
    )
    ax.set_yticks(range(3), ["English", "Vietnamese", "Chinese"])
    ax.set_title("Wrong budgets released by message language", loc="left", pad=12)
    ax.tick_params(length=0, pad=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.subplots_adjust(left=0.16, right=0.98, top=0.83, bottom=0.23)
    for ext in ["png", "svg"]:
        fig.savefig(outdir / f"language-heatmap.{ext}", dpi=300)
    plt.close(fig)
    with (outdir / "language-chart-data.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(source_rows[0]))
        writer.writeheader()
        writer.writerows(source_rows)

    budget_rows = []
    errors = {"absent": [], "present": []}
    for language in languages:
        for evidence in errors:
            subset = [
                r
                for r in trials
                if r["language"] == language
                and r["kind"] == "poisoned"
                and r["evidence"] == evidence
            ]
            assert len(subset) == 2
            wrong = sum(
                r["oracle"]["extracted_facts"]["budget"] != r["expected"]["budget"]
                for r in subset
            )
            errors[evidence].append(wrong)
        for task_index in [0, 1]:
            pair = {
                r["evidence"]: r
                for r in trials
                if r["source_case_id"].startswith(f"propagate-{task_index}-")
                and r["language"] == language
                and r["kind"] == "poisoned"
            }
            budget_rows.append(
                dict(
                    task=task_index,
                    language=language,
                    trusted_budget=pair["absent"]["expected"]["budget"],
                    no_record=pair["absent"]["oracle"]["extracted_facts"]["budget"],
                    with_record=pair["present"]["oracle"]["extracted_facts"]["budget"],
                )
            )
    fig, ax = plt.subplots(figsize=(9.2, 3.5))
    for evidence, offset, label, color, hatch in [
        ("absent", -0.19, "No trusted input", "#D38633", "///"),
        ("present", 0.19, "Trusted input", "#39749C", ""),
    ]:
        xs = [i + offset for i in range(3)]
        ax.bar(
            xs,
            errors[evidence],
            width=0.36,
            color=color,
            label=label,
            hatch=hatch,
            edgecolor="#333333",
            linewidth=0.6,
        )
        for x, count in zip(xs, errors[evidence]):
            ax.text(x, count + 0.07, f"{count} / 2", ha="center", fontsize=11)
    ax.set_xticks(range(3), ["English", "Vietnamese", "Chinese"])
    ax.set_ylim(0, 2.6)
    ax.set_yticks([0, 1, 2])
    ax.set_ylabel("Wrong budgets returned")
    ax.set_title("Worker errors before any release check", loc="left", pad=14)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper right", ncol=2, fontsize=10)
    fig.subplots_adjust(left=0.12, right=0.98, top=0.82, bottom=0.16)
    for ext in ["png", "svg"]:
        fig.savefig(outdir / f"budget-pairs.{ext}", dpi=300)
    plt.close(fig)
    with (outdir / "budget-chart-data.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(budget_rows[0]))
        writer.writeheader()
        writer.writerows(budget_rows)

    replay = {r["arm"]: r for r in metrics["archived_replay_groups"]}
    groups = ["strict_structural", "normalized_structural", "normalized_semantic"]
    assert (
        replay["strict_structural"]["blocked_correct_candidates"]
        == replay["strict_semantic"]["blocked_correct_candidates"]
    )
    assert (
        replay["strict_structural"]["target_budget_releases"]
        == replay["strict_semantic"]["target_budget_releases"]
    )
    fig, ax = plt.subplots(figsize=(9.2, 3.6))
    for key, offset, label, color, hatch in [
        ("target_budget_releases", -0.18, "Wrong reports released", "#D38633", "///"),
        (
            "blocked_correct_candidates",
            0.18,
            "Correct reports blocked",
            "#B7BEC6",
            "..",
        ),
    ]:
        ys = [i + offset for i in range(3)]
        values = [replay[arm][key] for arm in groups]
        ax.barh(
            ys,
            values,
            height=0.32,
            label=label,
            color=color,
            edgecolor="#333333",
            linewidth=0.6,
            hatch=hatch,
        )
        for y, count in zip(ys, values):
            ax.text(count + 0.08, y, str(count), va="center", fontsize=11)
    ax.set_yticks(
        range(3),
        [
            "Strict JSON\nboth checks",
            "Cleaned JSON\nstructure",
            "Cleaned JSON\nplus fact check",
        ],
    )
    ax.set_xlim(0, 7)
    ax.set_xticks(range(7))
    ax.set_ylim(2.6, -0.7)
    ax.set_xlabel("Reports (6 wrong and 6 correct in the saved set)")
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.47, 1.18),
        ncol=2,
        frameon=False,
        fontsize=10,
    )
    ax.spines[["top", "right"]].set_visible(False)
    fig.subplots_adjust(left=0.23, right=0.98, top=0.80, bottom=0.17)
    for ext in ["png", "svg"]:
        fig.savefig(outdir / f"archived-tradeoff.{ext}", dpi=300)
    plt.close(fig)
    exports = []
    for r in trials:
        peer = json.loads(json.loads(r["messages"][1]["content"])["peer_report"])
        exports.append(
            dict(
                trial_id=r["trial_id"],
                language=r["language"],
                kind=r["kind"],
                evidence=r["evidence"],
                expected=r["expected"],
                peer_report=peer,
                worker_response=json.loads(r["response"]["content"]),
                structural_allowed=r["checks"]["normalized_structural"]["allowed"],
                semantic_allowed=r["checks"]["normalized_semantic"]["allowed"],
                semantic_reasons=r["checks"]["normalized_semantic"]["reasons"],
            )
        )
    (outdir / "all-recorded-outputs.json").write_text(
        json.dumps(exports, ensure_ascii=False, indent=2) + "\n"
    )
    flat_fields = [
        "trial_id",
        "language",
        "kind",
        "evidence",
        "expected_budget",
        "worker_budget",
        "structural_allowed",
        "semantic_allowed",
        "public_summary",
    ]
    original = {r["trial_id"]: r for r in trials}
    with (outdir / "all-recorded-outputs.csv").open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=flat_fields)
        writer.writeheader()
        for row in exports:
            flat = {key: row[key] for key in flat_fields if key in row}
            flat["expected_budget"] = row["expected"]["budget"]
            flat["worker_budget"] = original[row["trial_id"]]["oracle"][
                "extracted_facts"
            ]["budget"]
            flat["public_summary"] = row["worker_response"]["public_summary"]
            writer.writerow(flat)
    provenance = json.loads((outdir / "provenance.json").read_text())
    provenance["trial_source"] = "runs/oversight-ablation-v1/trials.jsonl"
    provenance["trial_sha256"] = hashlib.sha256(trials_path.read_bytes()).hexdigest()
    provenance["language_cells"] = source_rows
    provenance["budget_pairs"] = budget_rows
    provenance["archived_replay"] = metrics["archived_replay_groups"]
    (outdir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print("Three additional figures and 24 exact saved output records exported.")


if __name__ == "__main__":
    main()
