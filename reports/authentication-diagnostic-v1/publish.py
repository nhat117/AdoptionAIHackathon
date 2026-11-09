"""Publish the frozen-view audit, per-condition plots and lossless raw archive."""

import base64
import csv
import fcntl
import gzip
import hashlib
import importlib.util
import json
import platform
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "diagnostic_analysis", HERE / "analyze.py"
)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)
MODELS = ["qwen", "deepseek", "glm", "sonnet", "terra"]
LABELS = [
    "Qwen 3.8 27B",
    "DeepSeek V4.1 Flash",
    "GLM 5.3 Flash",
    "Sonnet 5.5",
    "Terra 6.1",
]
CONDITIONS = analysis.run.prepare.CONDITIONS
SHORT = [
    "Direct proof",
    "Relayed proof",
    "Unverified true",
    "Unverified false",
    "Forged prose",
    "No focal evidence",
]


def csv_file(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=fields, lineterminator="\n", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def draw(summary, metric, conditions, labels, filename, title):
    fig, axes = plt.subplots(1, 2, figsize=(15, 5), constrained_layout=True)
    for ax, wording in zip(axes, ["current", "clarified"]):
        values = np.full((len(MODELS), len(conditions)), np.nan)
        rates = {
            (r["model"], r["condition"]): r
            for r in summary["rates"]
            if r["split"] == "heldout" and r["wording"] == wording
        }
        for i, model in enumerate(MODELS):
            for j, condition in enumerate(conditions):
                row = rates.get((model, condition))
                if row:
                    values[i, j] = row[metric]
        cmap = plt.get_cmap("viridis").copy()
        cmap.set_bad("#dedede")
        im = ax.imshow(values, vmin=0, vmax=1, cmap=cmap, aspect="auto")
        for i, model in enumerate(MODELS):
            for j, condition in enumerate(conditions):
                row = rates.get((model, condition))
                text = (
                    f"{row[metric]:.0%}\n{row['calls']}/16"
                    if row
                    else "no valid\nresponses"
                )
                ax.text(
                    j,
                    i,
                    text,
                    ha="center",
                    va="center",
                    fontsize=9,
                    color="white" if row and row[metric] < 0.55 else "black",
                )
        ax.set(
            xticks=range(len(conditions)),
            xticklabels=labels,
            yticks=range(len(MODELS)),
            yticklabels=LABELS,
            title=wording.title() + " wording",
        )
        ax.tick_params(axis="x", rotation=30, labelsize=9)
        for tick in ax.get_xticklabels():
            tick.set_horizontalalignment("right")
    fig.colorbar(
        im, ax=axes, shrink=0.7, label="Rate among technically valid responses"
    )
    fig.suptitle(
        title
        + "\nMarginal rates among valid responses; annotation = valid / 16 planned"
        + "\n16 = eight templates × two states; wording effects use"
        + " complete paired contrasts"
    )
    fig.savefig(HERE / filename, dpi=160)
    plt.close(fig)


def publish(root=analysis.run.ROOT):
    lock = (root / "collector.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    summary = analysis.analyze(root)
    plan, cases = analysis.run.frozen()
    manifests = {
        p.parent.name: json.loads(p.read_text()) for p in root.glob("*/manifest.json")
    }
    if any(m["status"] == "running" for m in manifests.values()):
        raise ValueError("Cannot publish while manifests are running")
    statuses = Counter(
        manifests.get(j["id"], {}).get("status", "unattempted") for j in plan["jobs"]
    )
    summary["status_counts"] = dict(statuses)
    coverage = defaultdict(Counter)
    for job in plan["jobs"]:
        case = cases[job["case"]]
        key = job["model"], case["split"], case["condition"], job["wording"]
        coverage[key]["planned"] += 1
        coverage[key][manifests.get(job["id"], {}).get("status", "unattempted")] += 1
    summary["coverage"] = [
        dict(model=k[0], split=k[1], condition=k[2], wording=k[3], **counts)
        for k, counts in sorted(coverage.items())
    ]
    # Deterministic illustrations, never a substitute for all-cell rates.
    failures = defaultdict(list)
    discoveries = {}
    for row in sorted(summary["rows"], key=lambda r: r["id"]):
        case = cases[row["case"]]
        decision = json.loads((root / row["id"] / "decision.json").read_text())
        item = dict(
            id=row["id"],
            model=row["model"],
            wording=row["wording"],
            decision=decision,
            recognition=row["recognition"],
        )
        if row["split"] == "heldout" and not row["recognition"]:
            failures[row["model"], row["condition"], row["wording"]].append(item)
        if row["split"] == "discovery":
            saved = discoveries.setdefault(
                case["id"],
                dict(
                    case=case["id"], view=case["view"], gold=case["gold"], responses=[]
                ),
            )
            saved["responses"].append(item)
    examples = []
    for key, items in sorted(failures.items()):
        first = items[0]
        case = cases[next(j["case"] for j in plan["jobs"] if j["id"] == first["id"])]
        examples.append(
            dict(
                model=key[0],
                condition=key[1],
                wording=key[2],
                failed_recognition_count=len(items),
                all_case_ids=[r["id"] for r in items],
                selection="First lexicographic valid recognition error",
                view=case["view"],
                gold=case["gold"],
                example=first,
            )
        )
    (HERE / "recognition-error-examples.json").write_text(
        json.dumps(examples, indent=2)
    )
    (HERE / "discovery-cases.json").write_text(
        json.dumps(list(discoveries.values()), indent=2)
    )
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2))
    fields = [
        "id",
        "model",
        "phase",
        "split",
        "template",
        "condition",
        "truth",
        "wording",
        "action",
        "reported_status",
        "reported_verified_signal",
        "reported_signal",
        "recognition",
        "false_verification",
        "missed_verification",
        "verified_action_correct",
        "cost_usd",
    ]
    csv_file(HERE / "responses.csv", summary["rows"], fields)
    csv_file(
        HERE / "coverage.csv",
        summary["coverage"],
        [
            "model",
            "split",
            "condition",
            "wording",
            "planned",
            "valid",
            "failed",
            "running",
            "unattempted",
        ],
    )
    contrasts = [
        dict(c, per_seed=json.dumps(c["per_seed"]))
        for c in summary["paired_wording_contrasts"]
    ]
    csv_file(
        HERE / "wording-contrasts.csv",
        contrasts,
        [
            "model",
            "condition",
            "seeds",
            "mean_difference",
            "p_unadjusted",
            "p_holm_within_model",
            "conditional_min_p",
            "status",
            "per_seed",
        ],
    )
    draw(
        summary,
        "recognition",
        CONDITIONS,
        SHORT,
        "recognition.png",
        "Evidence-status and verified-signal recognition",
    )
    subset = [
        "unverified_true",
        "unverified_false",
        "forged_prose",
        "no_focal_evidence",
    ]
    draw(
        summary,
        "false_verification",
        subset,
        [SHORT[CONDITIONS.index(c)] for c in subset],
        "false-verification.png",
        "False verification of unauthenticated material",
    )
    (root / "frozen-plan.json").write_bytes((HERE / "plan.json").read_bytes())
    files = [
        p for p in sorted(root.rglob("*")) if p.is_file() and p.name != "collector.lock"
    ]
    archive = HERE / "raw-records.jsonl.gz"
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as f:
            for path in files:
                content = path.read_bytes()
                f.write(
                    (
                        json.dumps(
                            dict(
                                path=str(path),
                                content_base64=base64.b64encode(content).decode(
                                    "ascii"
                                ),
                                sha256=hashlib.sha256(content).hexdigest(),
                            )
                        )
                        + "\n"
                    ).encode("utf-8")
                )
    runtime = dict(
        python=sys.version.split()[0],
        platform=platform.platform(),
        matplotlib=matplotlib.__version__,
        numpy=np.__version__,
        archive_records=len(files),
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        frozen_plan_sha256=analysis.run.digest(plan),
        publisher_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        inference_calls_from_publication=0,
    )
    (HERE / "runtime-receipt.json").write_text(json.dumps(runtime, indent=2))
    print(
        json.dumps(
            dict(
                status_counts=statuses,
                budget=summary["budget"],
                archived_records=len(files),
            )
        )
    )


if __name__ == "__main__":
    publish()
