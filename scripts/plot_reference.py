import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

root = Path(__file__).resolve().parents[1]
m = json.loads((root / "runs/reference-deepset-adaption/metrics.json").read_text())
fig, axs = plt.subplots(1, 2, figsize=(10, 4.4), gridspec_kw={"width_ratios": [1, 1.3]})
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
a = axs[0]
matrix = [[m["tn"], m["fp"]], [m["fn"], m["tp"]]]
a.imshow(matrix, cmap="Blues", vmin=0, vmax=60)
for i in range(2):
    for j in range(2):
        a.text(
            j,
            i,
            str(matrix[i][j]),
            ha="center",
            va="center",
            fontsize=23,
            color="white" if matrix[i][j] > 35 else "#14263b",
        )
a.set_xticks([0, 1], ["Ordinary", "Injection"])
a.set_yticks([0, 1], ["Ordinary", "Injection"])
a.set_xlabel("Predicted label")
a.set_ylabel("Dataset label")
a.set_title("Reference test: exact counts", loc="left", pad=15)
b = axs[1]
values = [m["recall"], m["false_positive_rate"]]
cis = [m["recall_wilson95"], m["fpr_wilson95"]]
b.barh([1, 0], values, color=["#166b86", "#d06b38"], height=0.44)
b.errorbar(
    values,
    [1, 0],
    xerr=[
        [max(0, v - c[0]) for v, c in zip(values, cis)],
        [c[1] - v for v, c in zip(values, cis)],
    ],
    fmt="none",
    color="#14263b",
    capsize=4,
)
b.set_yticks([1, 0], ["Injection recall", "False-positive rate"])
b.set_xlim(0, 1)
b.xaxis.set_major_formatter(PercentFormatter(1))
b.grid(axis="x", alpha=0.2)
b.set_axisbelow(True)
for y, v in zip([1, 0], values):
    b.text(min(v + 0.025, 0.93), y + 0.19, f"{v:.1%}", fontsize=11, weight="bold")
b.set_title("DeepSeek V4 Flash via Adaption", loc="left", pad=15)
for spine in ["top", "right"]:
    b.spines[spine].set_visible(False)
fig.suptitle(
    "Detection on 116 public test examples",
    x=0.06,
    ha="left",
    fontsize=17,
    weight="bold",
)
fig.text(
    0.06,
    0.025,
    (
        "60 injection / 56 ordinary labels · Wilson intervals assume independence.\n"
        "No prompt tuning or training. Detection labels do not measure end-to-end "
        "agent protection."
    ),
    fontsize=9,
    color="#435266",
)
fig.tight_layout(rect=[0, 0.12, 1, 0.91])
out = root / "research/figures"
out.mkdir(exist_ok=True)
fig.savefig(out / "adaption-reference.png", dpi=190, bbox_inches="tight")
fig.savefig(out / "adaption-reference.svg", bbox_inches="tight")
