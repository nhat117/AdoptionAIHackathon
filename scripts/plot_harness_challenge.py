"""Plot controlled-fault counts and live paired results as separate evidence."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
r = json.loads((ROOT / "research/HARNESS_CHALLENGE_METRICS.json").read_text())
v1 = r["controlled_faults"]["original"]
v2 = r["controlled_faults"]["updated"]
live = r["live"]
fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))
a = axes[0]
counts = [v2["unsafe"], v1["unsafe_released"], v2["unsafe_released"]]
a.bar(range(3), counts, color=["#74828c", "#d06b38", "#267b67"], width=0.58)
a.set_xticks(range(3), ["No gate\n(passthrough)", "Original\ngate", "Updated\ngate"])
a.set_ylim(0, v2["unsafe"] * 1.2)
a.set_ylabel("Unsafe candidates released")
a.set_title("Controlled compromised-generator outputs", loc="left", fontsize=11)
for x, n in enumerate(counts):
    a.text(x, n + 3, f"{n}/{v2['unsafe']}", ha="center", weight="bold", fontsize=11)
b = axes[1]
unsafe = [
    live["baseline_attack_policy_violations"],
    live["protected_attack_violations_released"],
]
benign = [
    live["baseline_benign_contract_completion"],
    live["protected_benign_contract_completion"],
]
x = [0, 1]
b.bar(
    [i - 0.18 for i in x],
    unsafe,
    width=0.32,
    color="#d06b38",
    label="Unsafe attack output",
)
b.bar(
    [i + 0.18 for i in x],
    benign,
    width=0.32,
    color="#166b86",
    label="Benign completion",
)
b.set_xticks(x, ["Without runtime\nharness", "Updated runtime\nharness"])
b.set_ylabel("Live cases")
b.set_ylim(0, max(benign + unsafe + [1]) * 1.3)
b.set_title("Live paired Adaption model evaluation", loc="left", fontsize=11)
for i in x:
    b.text(
        i - 0.18,
        unsafe[i] + 1,
        f"{unsafe[i]}/{live['attack_cases']}",
        ha="center",
        color="#b85222",
        fontsize=10,
    )
    b.text(
        i + 0.18,
        benign[i] + 1,
        f"{benign[i]}/{live['benign_cases']}",
        ha="center",
        color="#145468",
        fontsize=10,
    )
b.legend(
    frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=9
)
for ax in axes:
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
fig.suptitle(
    "Reporting harness: controlled enforcement and live comparison",
    x=0.07,
    ha="left",
    fontsize=16,
    weight="bold",
)
fig.text(
    0.07,
    0.035,
    (
        "Controlled benign fixtures preserved: "
        f"original {v1['benign_released']}/{v1['benign']}, "
        f"updated {v2['benign_released']}/{v2['benign']}.\n"
        "Constructed faults and live model attacks are separate datasets; "
        "their results are not pooled."
    ),
    fontsize=10,
    color="#435266",
)
fig.tight_layout(rect=[0, 0.24, 1, 0.89])
out = ROOT / "research/figures"
out.mkdir(exist_ok=True)
fig.savefig(out / "harness-challenge.png", dpi=190, bbox_inches="tight")
fig.savefig(out / "harness-challenge.svg", bbox_inches="tight")
