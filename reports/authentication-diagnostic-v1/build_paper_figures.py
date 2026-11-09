"""Build paper-only illustrations from frozen summaries; never alter study scoring.

Run from any directory with a Python environment containing matplotlib.
The PNG figures are local to the existing LaTeX project. No PDF is exported.
"""

import csv
import json
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/adoptionai-paper-matplotlib")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "projects/persistent-dissenter/figures"
OUT.mkdir(exist_ok=True)
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)
INK, BLUE, TEAL, RED, GRAY = "#172e46", "#276da5", "#258577", "#a64745", "#e1e5e9"


def box(ax, x, y, w, h, title, body, color=BLUE):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012",
            linewidth=1,
            edgecolor=color,
            facecolor="#f7f9fb",
        )
    )
    ax.text(
        x + w / 2,
        y + h - 0.055,
        title,
        ha="center",
        va="top",
        weight="bold",
        color=color,
        fontsize=10,
    )
    ax.text(
        x + w / 2,
        y + h / 2 - 0.035,
        body,
        ha="center",
        va="center",
        color=INK,
        fontsize=9,
        linespacing=1.45,
    )


def arrow(ax, x1, y, x2):
    ax.annotate(
        "", (x2, y), (x1, y), arrowprops={"arrowstyle": "->", "color": INK, "lw": 1.3}
    )


def overview():
    fig, ax = plt.subplots(figsize=(7, 3.0))
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    ax.text(
        0.01,
        0.98,
        "A  INTERACTING NETWORKS",
        weight="bold",
        color=INK,
        va="top",
        fontsize=11,
    )
    # Degree-four ring: ten actual nodes, two distinct controlled roles.
    cx, cy, radius = 0.12, 0.70, 0.095
    pts = [
        (
            cx + radius * math.cos(2 * math.pi * i / 10),
            cy + 0.14 * math.sin(2 * math.pi * i / 10),
        )
        for i in range(10)
    ]
    for i in range(10):
        for step in (1, 2):
            j = (i + step) % 10
            ax.plot(
                [pts[i][0], pts[j][0]],
                [pts[i][1], pts[j][1]],
                lw=0.6,
                color="#c6cfd8",
                zorder=0,
            )
    for i, (x, y) in enumerate(pts):
        ax.scatter(
            x,
            y,
            s=72,
            c=TEAL if i == 0 else RED if i == 5 else BLUE,
            edgecolors="white",
            zorder=2,
        )
    ax.text(0.12, 0.495, "10 agents · degree 4", ha="center", fontsize=8)
    ax.text(0.12, 0.46, "Witness (green)", ha="center", fontsize=7.5, color=TEAL)
    ax.text(0.12, 0.423, "Broadcaster (red)", ha="center", fontsize=7.5, color=RED)
    arrow(ax, 0.235, 0.71, 0.28)
    box(
        ax,
        0.29,
        0.51,
        0.30,
        0.36,
        "THREE EVIDENCE ARMS",
        "Text testimony\nTruthful unverified capsule\nAuthenticated capsule",
    )
    arrow(ax, 0.605, 0.71, 0.65)
    box(
        ax,
        0.66,
        0.51,
        0.32,
        0.36,
        "REPEAT, THEN SCORE",
        "Read → message + action\nAutomatic capsule forwarding\nFinal stay / evacuate",
    )
    ax.text(
        0.82,
        0.45,
        "2 configurations × 8 seeds × 3 arms\n48 games",
        ha="center",
        fontsize=7.5,
        va="center",
    )
    ax.axhline(0.405, color="#ccd4dc", lw=0.8)
    ax.text(
        0.01,
        0.375,
        "B  SEPARATE FROZEN-VIEW DIAGNOSTIC",
        weight="bold",
        color=INK,
        va="top",
        fontsize=11,
    )
    box(
        ax,
        0.015,
        0.035,
        0.27,
        0.27,
        "MATCHED INPUTS",
        "8 templates × 2 states\n6 evidence conditions",
        TEAL,
    )
    arrow(ax, 0.30, 0.17, 0.335)
    box(
        ax,
        0.35,
        0.035,
        0.285,
        0.27,
        "FIVE CONFIGURATIONS",
        "Current / clarified wording\n192 held-out attempts each",
        TEAL,
    )
    arrow(ax, 0.65, 0.17, 0.685)
    box(
        ax,
        0.70,
        0.035,
        0.28,
        0.27,
        "SCORE SEPARATELY",
        "Output validity\nEvidence label + action",
        TEAL,
    )
    fig.subplots_adjust(left=0.015, right=0.985, top=0.99, bottom=0.02)
    fig.savefig(OUT / "study-overview.png", dpi=300, facecolor="white")
    plt.close(fig)


def results():
    network = json.loads(
        (ROOT / "reports/evidence-controls-v3/summary.json").read_text()
    )
    arms = {}
    for c in network["contrasts"]:
        if c["section"] != "5b":
            continue
        for s in c["per_seed"]:
            for field in ("treatment", "control"):
                key = (c["model"], c[field], s["seed"])
                assert key not in arms or arms[key] == s[field]
                arms[key] = s[field]
    rows = list(
        csv.DictReader(
            (ROOT / "reports/authentication-diagnostic-v1/responses.csv").open()
        )
    )
    held = [r for r in rows if r["split"] == "heldout"]
    models = ["qwen", "deepseek", "glm", "sonnet", "terra"]
    totals = []
    for m in models:
        selected = [r for r in held if r["model"] == m]
        correct = sum(int(r["recognition"]) for r in selected)
        totals.append(
            {
                "model": m,
                "planned": 192,
                "valid": len(selected),
                "correct_valid": correct,
                "incorrect_valid": len(selected) - correct,
                "invalid": 192 - len(selected),
                "lower_success": correct / 192,
                "upper_if_all_invalid_correct": (correct + 192 - len(selected)) / 192,
            }
        )
    assert sum(t["invalid"] for t in totals) == 16
    assert sum(t["correct_valid"] for t in totals) == 923
    with (Path(__file__).parent / "paper-planned-denominators.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(totals[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(totals)

    fig = plt.figure(figsize=(7, 2.75))
    grid = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.4], wspace=0.43)
    for panel, model, title, color in [
        (0, "sonnet", "A  Sonnet / Google", BLUE),
        (1, "terra", "B  Terra / OpenAI", TEAL),
    ]:
        ax = fig.add_subplot(grid[0, panel])
        names = ["private_text", "private_unverified", "private_proof"]
        for seed in range(2000, 2008):
            ys = [100 * arms[(model, name, seed)] for name in names]
            # A small fixed seed offset reveals coincident points without altering y.
            offset = (seed - 2003.5) * 0.017
            ax.plot(
                [x + offset for x in range(3)],
                ys,
                color=color,
                lw=0.65,
                alpha=0.5,
                marker="o",
                ms=3,
            )
        means = [
            100 * sum(arms[(model, n, s)] for s in range(2000, 2008)) / 8 for n in names
        ]
        ax.plot(range(3), means, color=INK, marker="D", ms=4, lw=1.5)
        for x, y in enumerate(means):
            label = f"{y:.1f}".rstrip("0").rstrip(".") + "%"
            ax.annotate(
                label,
                (x, y),
                (0, 9 if y < 90 else -17),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                weight="bold",
            )
        ax.set_title(title, loc="left", fontsize=9, weight="bold", pad=9)
        ax.set(
            ylim=(-5, 108),
            xlim=(-0.23, 2.23),
            xticks=range(3),
            xticklabels=["Text", "Unverified", "Verified"],
            yticks=[0, 50, 100],
        )
        ax.tick_params(axis="x", labelsize=8)
        ax.grid(axis="y", alpha=0.18)
        if panel == 0:
            ax.set_ylabel("Correct final action (%)", fontsize=9)
        ax.set_xlabel("8 paired seeds", fontsize=8, labelpad=9)
    ax = fig.add_subplot(grid[0, 2])
    ax.set_title(
        "C  Held-out recognition", loc="left", fontsize=9, weight="bold", pad=9
    )
    ys = list(range(5))
    ax.barh(ys, [t["correct_valid"] for t in totals], color=TEAL, label="Correct valid")
    ax.barh(
        ys,
        [t["incorrect_valid"] for t in totals],
        left=[t["correct_valid"] for t in totals],
        color=RED,
        label="Incorrect valid",
    )
    ax.barh(
        ys,
        [t["invalid"] for t in totals],
        left=[t["valid"] for t in totals],
        color=GRAY,
        hatch="////",
        edgecolor="#79848e",
        linewidth=0.4,
        label="Invalid",
    )
    for y, t in enumerate(totals):
        ax.text(
            4,
            y,
            f"{t['correct_valid']} / {t['incorrect_valid']} / {t['invalid']}",
            va="center",
            color="white",
            fontsize=8,
        )
    ax.set(
        yticks=ys,
        yticklabels=["Qwen", "DeepSeek", "GLM", "Sonnet", "Terra"],
        xlim=(0, 192),
        xticks=[0, 96, 192],
    )
    ax.invert_yaxis()
    ax.set_xlabel("Correct / incorrect / invalid counts", fontsize=8)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.24),
        ncol=1,
        fontsize=7,
        frameon=False,
        handlelength=1.2,
        labelspacing=0.3,
    )
    fig.subplots_adjust(left=0.08, right=0.97, top=0.86, bottom=0.31)
    fig.savefig(OUT / "evidence-results.png", dpi=300, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    overview()
    results()
