"""Plot saved 600-case counts; requires matplotlib (no inference calls)."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[1]
m = json.loads((ROOT / "research/AUTHORITY600_METRICS.json").read_text())
rows = m["conditions"]
fig, axes = plt.subplots(
    1, 2, figsize=(10, 4.8), gridspec_kw={"width_ratios": [1.2, 1]}
)
colors = {"peer": "#166b86", "authority": "#d06b38"}
a = axes[0]
for role, offset in [("peer", -0.12), ("authority", 0.12)]:
    rr = [r for r in rows if r["role"] == role]
    y = [r["disclosure_rate"] for r in rr]
    x = [i + offset for i in range(3)]
    lo = [max(0, v - r["wilson95_low"]) for v, r in zip(y, rr)]
    hi = [max(0, r["wilson95_high"] - v) for v, r in zip(y, rr)]
    a.errorbar(
        x,
        y,
        yerr=[lo, hi],
        fmt="o",
        color=colors[role],
        capsize=4,
        markersize=6,
        label="Peer" if role == "peer" else "Director",
    )
    for i, r in enumerate(rr):
        a.annotate(
            f"{r['marker_disclosures']}/{r['returned_attacks']}",
            (x[i], y[i]),
            xytext=(-10 if role == "peer" else 10, 10),
            textcoords="offset points",
            ha="right" if role == "peer" else "left",
            fontsize=9,
            color=colors[role],
        )
max_ci = max(r["wilson95_high"] or 0 for r in rows)
a.set_ylim(-0.004, 0.1 if max_ci <= 0.09 else min(1, max_ci * 1.15))
a.set_xticks([0, 1, 2], ["English", "Vietnamese", "Chinese"])
a.yaxis.set_major_formatter(PercentFormatter(1))
a.set_ylabel("Marker disclosure rate")
a.set_title("Attack outcomes: 90 tasks per sender / language", fontsize=11, loc="left")
a.grid(axis="y", alpha=0.2)
a.set_axisbelow(True)
a.legend(frameon=False, loc="upper right")
b = axes[1]
xx = list(range(3))
attack = [r["attack_responses"] for r in m["languages"]]
benign = [r["benign_responses"] for r in m["languages"]]
b.bar(xx, attack, color="#166b86", width=0.6, label="Attack")
b.bar(xx, benign, bottom=attack, color="#d06b38", width=0.6, label="Benign")
b.set_ylim(0, 225)
b.set_xticks(xx, ["English", "Vietnamese", "Chinese"])
b.set_ylabel("Returned target responses")
b.set_title("Exactly 200 planned cases per language", fontsize=11, loc="left")
for i, r in enumerate(m["languages"]):
    b.text(
        i,
        r["returned"] + 4,
        f"{r['returned']}/200",
        ha="center",
        fontsize=11,
        weight="bold",
    )
    b.text(i, attack[i] / 2, str(attack[i]), ha="center", color="white", fontsize=11)
    b.text(
        i,
        attack[i] + benign[i] / 2,
        str(benign[i]),
        ha="center",
        va="center",
        color="white",
        fontsize=10,
    )
b.legend(
    frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2, fontsize=10
)
b.grid(axis="y", alpha=0.2)
b.set_axisbelow(True)
for ax in axes:
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
fig.suptitle(
    "Adaption Gemma: the 600-case authority and language study",
    x=0.07,
    ha="left",
    fontsize=15,
    weight="bold",
)
fig.text(
    0.07,
    0.025,
    (
        "Left: 95% Wilson intervals assume independent tasks within a condition. "
        "Reused tasks pair the conditions.\n"
        "Zero observed leaks do not establish general safety or absence of "
        "authority and language effects."
    ),
    fontsize=9,
    color="#435266",
)
fig.tight_layout(rect=[0, 0.22, 1, 0.91])
out = ROOT / "research/figures"
out.mkdir(exist_ok=True)
fig.savefig(out / "authority600.png", dpi=190, bbox_inches="tight")
fig.savefig(out / "authority600.svg", bbox_inches="tight")
