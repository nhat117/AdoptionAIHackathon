"""Optional scientific figure from completed runs (requires matplotlib)."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folders", type=Path, nargs="+")
    parser.add_argument("--out", type=Path, default=Path("research/figures"))
    args = parser.parse_args()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    args.out.mkdir(parents=True, exist_ok=True)
    summaries = [
        json.loads((folder / "metrics.json").read_text()) for folder in args.folders
    ]
    fig, axes = plt.subplots(
        1, len(summaries), figsize=(6 * len(summaries), 4.8), squeeze=False
    )
    for ax, summary in zip(axes[0], summaries):
        for i, role in enumerate(["peer", "authority"]):
            cells = [c for c in summary["cells"] if c["authority"] == role]
            bars = ax.bar(
                [j + (i - 0.5) * 0.36 for j in range(3)],
                [100 * c["asr"]["rate"] for c in cells],
                0.34,
                color=["#286b8d", "#ce7939"][i],
                label=["Ordinary peer", "Fictional director"][i],
            )
            for bar, cell in zip(bars, cells):
                metric = cell["asr"]
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 1.5,
                    f"{metric['numerator']}/{metric['denominator']}",
                    ha="center",
                    fontsize=9,
                )
        ax.set_xticks(range(3), ["English", "Vietnamese", "Chinese"])
        ax.set_ylim(0, 100)
        ax.set_ylabel("Normalized marker disclosure (%)")
        ax.set_title(", ".join(summary["returned_target_models"]), loc="left")
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(frameon=False, fontsize=9)
    fig.suptitle(
        "Authority x language: fixed correction template",
        x=0.06,
        ha="left",
        fontweight="bold",
        fontsize=15,
    )
    fig.text(
        0.06,
        0.025,
        "Each attack cell: 20 tasks x 3 repetitions. "
        "Machine-authored translations; independent bilingual review pending.",
        fontsize=9,
    )
    fig.tight_layout(rect=[0.01, 0.06, 1, 0.92])
    fig.savefig(args.out / "h1-primary-asr.png", dpi=180)
    fig.savefig(args.out / "h1-primary-asr.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
