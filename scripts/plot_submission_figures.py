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

    fig, axs = plt.subplots(1, 2, figsize=(9.4, 3.4), sharex=True, sharey=True)
    budget_rows = []
    for task_index, ax in enumerate(axs):
        prefix = f"propagate-{task_index}-"
        subset = [
            r
            for r in trials
            if r["source_case_id"].startswith(prefix) and r["kind"] == "poisoned"
        ]
        expected = subset[0]["expected"]["budget"]
        ax.axvline(
            expected,
            color="#333333",
            linestyle="--",
            linewidth=1,
            label="Trusted budget",
        )
        for y, language in enumerate(languages):
            pair = {r["evidence"]: r for r in subset if r["language"] == language}
            before = pair["absent"]["oracle"]["extracted_facts"]["budget"]
            after = pair["present"]["oracle"]["extracted_facts"]["budget"]
            ax.plot([before, after], [y, y], color="#AAAAAA", linewidth=1.5)
            ax.scatter(
                before,
                y,
                color="#D38633",
                marker="s",
                s=75,
                label="No worker record" if y == 0 else None,
                zorder=3,
            )
            ax.scatter(
                after,
                y,
                color="#39749C",
                marker="o",
                s=75,
                label="Worker has record" if y == 0 else None,
                zorder=3,
            )
            budget_rows.append(
                dict(
                    task=task_index,
                    language=language,
                    trusted_budget=expected,
                    no_record=before,
                    with_record=after,
                )
            )
        ax.set_title(
            f"Task {task_index + 1}: trusted budget {expected:,}",
            loc="left",
            fontsize=11,
        )
        ax.set_yticks(range(3), ["English", "Vietnamese", "Chinese"])
        ax.set_ylim(2.5, -0.5)
        ax.set_xlim(11500, 14000)
        ax.set_xticks([12000, 13000, 14000])
        ax.set_xlabel("Recorded worker budget")
        ax.spines[["top", "right"]].set_visible(False)
    handles, labels = axs[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.54, 0.99),
        fontsize=9,
    )
    fig.subplots_adjust(left=0.13, right=0.96, top=0.73, bottom=0.19, wspace=0.15)
    for ext in ["png", "svg"]:
        fig.savefig(outdir / f"budget-pairs.{ext}", dpi=300)
    plt.close(fig)
    with (outdir / "budget-chart-data.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(budget_rows[0]))
        writer.writeheader()
        writer.writerows(budget_rows)

    replay = {r["arm"]: r for r in metrics["archived_replay_groups"]}
    fig, ax = plt.subplots(figsize=(8.5, 3.7))
    points = [
        ("strict_structural", "Strict parsing: both checks", (12, -16)),
        ("normalized_structural", "Shared cleaning: structural", (-198, 16)),
        ("normalized_semantic", "Shared cleaning: plus fact check", (12, 16)),
    ]
    assert (
        replay["strict_structural"]["blocked_correct_candidates"]
        == replay["strict_semantic"]["blocked_correct_candidates"]
    )
    for arm, label, offset in points:
        r = replay[arm]
        x, y = r["target_budget_releases"], r["blocked_correct_candidates"]
        ax.scatter(x, y, s=85, color="#39749C", edgecolor="#222222", zorder=3)
        ax.annotate(
            label, (x, y), xytext=offset, textcoords="offset points", fontsize=10
        )
    ax.set_xlim(-0.5, 7)
    ax.set_ylim(-0.6, 7)
    ax.set_xticks(range(7))
    ax.set_yticks(range(7))
    ax.set_xlabel("Wrong budgets released (out of 6 wrong reports)")
    ax.set_ylabel("Correct reports blocked\n(out of 6 correct reports)")
    ax.grid(color="#E6E6E6", linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    fig.subplots_adjust(left=0.16, right=0.98, top=0.94, bottom=0.19)
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
