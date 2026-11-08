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
        "notes": ("24 unique responses. Paired checks reuse candidates. "
                  "Blocked reports are not repaired. No new inference."),
    }
    (args.outdir / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n"
    )
    print("Both figures rendered with Matplotlib", matplotlib.__version__)


if __name__ == "__main__":
    main()
