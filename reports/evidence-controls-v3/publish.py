"""Publish replay-audited v3 tables, figures and restorable raw records."""

import csv
import fcntl
import gzip
import importlib.util
import json
from collections import Counter
from pathlib import Path
from statistics import mean

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("v3analysis", HERE / "analyze.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def publish(root=Path("runs/evidence-controls-v3")):
    collector_lock = (root / "collector.lock").open("a")
    fcntl.flock(collector_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    games, missing, audits, budget, plan = analysis.audit_module().collect(root)
    if budget["pending"]:
        raise ValueError("Unresolved billing: checkpoint approval withheld")
    summary = analysis.analyse(games, missing)
    for contrast in summary["contrasts"]:
        nonzero = sum(
            abs(p["treatment"] - p["control"]) > 1e-12 for p in contrast["per_seed"]
        )
        contrast["nonzero_pairs"] = nonzero
        contrast["conditional_min_attainable_p"] = (
            min(1, 2 / 2**nonzero) if contrast["complete_pairs"] else None
        )
        contrast["min_attainable_p_interpretation"] = (
            "Nominal best case if every complete pair has a nonzero difference; "
            "conditional minimum accounts for observed zero differences."
        )
    summary.update(
        audits=audits,
        budget=budget,
        planned=len(plan["jobs"]),
        completed=len(games),
        replayed_completed=len(audits),
    )
    statuses = Counter()
    cells = {}
    attempts = returned = 0
    for job in plan["jobs"]:
        path = root / job["id"] / "manifest.json"
        manifest = json.loads(path.read_text()) if path.exists() else {}
        status = manifest.get("status", "unattempted")
        statuses[status] += 1
        key = (
            job["section"],
            job["model_tag"],
            job["scenario"]["disaster"],
            job["arm"],
        )
        cell = cells.setdefault(key, Counter())
        cell["planned"] += 1
        cell[status] += 1
        attempts += manifest.get("decision_attempts", 0)
        returned += sum(
            row["type"] == "provider_metadata"
            for row in analysis.audit_module().records(path.parent / "calls.jsonl")
        )
    summary.update(
        status_counts=dict(statuses),
        decision_attempts=attempts,
        returned_provider_calls=returned,
        collection_cells=[
            dict(section=k[0], model=k[1], disaster=k[2], arm=k[3], **counts)
            for k, counts in sorted(cells.items())
        ],
    )
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2))
    (HERE / "plan.json").write_bytes((root / "plan.json").read_bytes())
    rows = []
    for key, outcome in sorted(games.items()):
        section, model, disaster, seed, arm = key
        correct = outcome[analysis.OUTCOME[section]]
        rows.append(
            dict(
                section=section,
                model=model,
                disaster=disaster,
                seed=seed,
                arm=arm,
                correct=correct,
                miss_rate=1 - outcome["correct_action_rate"] if disaster else None,
                false_alarm_rate=1 - outcome["correct_action_rate"]
                if not disaster
                else None,
                claim_following_rate=1 - outcome["correct_action_rate"],
                recipient_correct=outcome["correct_action_rate"],
                nonwitness_correct=outcome["other_recipients_correct_action_rate"],
            )
        )
    if rows:
        with (HERE / "games.csv").open("w") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    figure(
        rows,
        "5b",
        [("sonnet", True), ("terra", True)],
        ["private_text", "private_unverified", "private_proof"],
        ["Text testimony", "Unverified capsule", "Verified capsule"],
        "Non-witness correct action in disaster games",
        "content-vs-authentication.png",
    )
    figure(
        rows,
        "6",
        [("sonnet", True), ("terra", True), ("terra", False)],
        ["none", "delayed"],
        ["No truth", "Truth usable round 3"],
        "Final recipient correct action: delayed truth",
        "delayed-truth.png",
    )
    files = [
        p for p in sorted(root.rglob("*")) if p.is_file() and p.name != "collector.lock"
    ]
    files += [Path(p) for p in plan["prior_ledger_sha256"]]
    with (HERE / "raw-records.jsonl.gz").open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as f:
            for path in files:
                line = json.dumps(dict(path=str(path), content=path.read_text())) + "\n"
                f.write(line.encode("utf-8"))
    print(json.dumps(dict(completed=len(games), missing=len(missing), budget=budget)))


def figure(rows, section, cells, arms, labels, title, filename):
    fig, axes = plt.subplots(1, len(cells), figsize=(6 * len(cells), 4), squeeze=False)
    for ax, (model, disaster) in zip(axes[0], cells):
        for x, arm in enumerate(arms):
            values = [
                r["correct"]
                for r in rows
                if r["section"] == section
                and r["model"] == model
                and r["disaster"] == disaster
                and r["arm"] == arm
            ]
            if values:
                ax.bar(
                    x,
                    mean(values),
                    color=["#8999ae", "#eaac55", "#388f88"][x],
                    alpha=0.65,
                )
                ax.scatter(
                    [
                        x + (i - (len(values) - 1) / 2) * 0.035
                        for i in range(len(values))
                    ],
                    values,
                    color="#25364c",
                    s=22,
                )
                ax.text(x, 1.04, f"n={len(values)} games", ha="center", fontsize=9)
            else:
                ax.text(x, 0.1, "no complete games", ha="center", fontsize=9)
        ax.set(
            xticks=range(len(arms)),
            xticklabels=labels,
            ylim=(0, 1.15),
            xlim=(-0.6, len(arms) - 0.4),
            title=f"{model.title()} / {'disaster' if disaster else 'safe'}",
        )
        ax.tick_params(axis="x", labelsize=9)
        ax.set_yticks([0, 0.5, 1], ["0%", "50%", "100%"])
        ax.spines[["top", "right"]].set_visible(False)
    axes[0][0].set_ylabel("Correct-action rate")
    fig.suptitle(title)
    fig.text(
        0.5,
        0.015,
        "Dots are whole games; seeds are replicates. Exploratory, English only.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.045, 1, 0.94))
    fig.savefig(HERE / filename, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    publish()
