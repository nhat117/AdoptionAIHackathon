"""Post-hoc citation-linked exposure, not endorsement or semantic propagation."""

import argparse
import json
from pathlib import Path


def main(root):
    rows = []
    for manifest_path in sorted(root.glob("*/manifest.json")):
        m = json.loads(manifest_path.read_text())
        if m["status"] != "completed":
            continue
        source = m["scenario"]["informant"]
        linked, direct, exposed = set(), set(), set()
        rounds = []
        outcome = json.loads((manifest_path.parent / "outcome.json").read_text())
        adjacency = outcome["adjacency"]
        traces = [
            json.loads(x)
            for x in (manifest_path.parent / "traces.jsonl").read_text().splitlines()
        ]
        for trace in traces:
            # Parents reference received earlier-round messages, so current outputs
            # cannot cite one another and iteration order cannot create a cascade.
            for sender, message in trace["messages"].items():
                if int(sender) == source or linked.intersection(message["parents"]):
                    linked.add(message["id"])
            # Delivery after this round; exposure can influence the next decision.
            for recipient in trace["views"]:
                if int(recipient) == source:
                    continue
                for sender, message in trace["messages"].items():
                    if int(sender) in adjacency[recipient]:
                        if int(sender) == source:
                            direct.add(int(recipient))
                        if message["id"] in linked:
                            exposed.add(int(recipient))
            rounds.append(
                dict(
                    round=trace["round"],
                    direct_recipients=len(direct),
                    citation_linked_recipients=len(exposed),
                )
            )
        rows.append(
            dict(
                id=m["id"],
                section=m["section"],
                scenario=m["scenario"].get("id", m["id"]),
                seed=m["scenario"].get("seed"),
                language=m["language"],
                identity=m["identity"],
                topology=m["topology"],
                rounds=rounds,
            )
        )
    baseline = {(r["scenario"], r["language"]): r for r in rows if r["section"] == 1}
    pairs = []
    for r in rows:
        if r["section"] != 3:
            continue
        b = baseline.get((r["scenario"], r["language"]))
        if b:
            treatment = next(
                t["citation_linked_recipients"] for t in r["rounds"] if t["round"] == 2
            )
            control = next(
                t["citation_linked_recipients"] for t in b["rounds"] if t["round"] == 2
            )
            pairs.append(
                dict(
                    scenario=r["scenario"],
                    seed=r["seed"],
                    language=r["language"],
                    second_round_recipient_difference=treatment - control,
                )
            )
    output = Path("reports/overnight-experiments/propagation.json")
    output.write_text(
        json.dumps(
            dict(
                purpose="post_hoc_exploratory_diagnostic",
                definition=(
                    "Cumulative recipients of source messages or "
                    "citation-linked descendants"
                ),
                limitations=(
                    "Citation can dispute a claim; this does not establish belief, "
                    "agreement or semantic preservation."
                ),
                timing=(
                    "Exposure measured after delivery; "
                    "actionable from the following round."
                ),
                games=rows,
                post_hoc_network_pairs=pairs,
            ),
            indent=2,
        )
    )
    plot(rows)
    print("Completed games with propagation diagnostics:", len(rows))


def plot(rows):
    import matplotlib

    matplotlib.use("Agg")
    from statistics import mean

    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    for section, ax in enumerate(axes, 1):
        selected = [
            r
            for r in rows
            if r["section"] == section
            or (
                section in (2, 3)
                and r["section"] == 1
                and (section == 3 or "calibration-000" in r["id"])
            )
        ]
        field = {1: "language", 2: "identity", 3: "topology"}[section]
        groups = sorted({r[field] for r in selected})
        for group in groups:
            rs = [r for r in selected if r[field] == group]
            xs = sorted({t["round"] for r in rs for t in r["rounds"]})
            ys = [
                mean(
                    t["citation_linked_recipients"] / 9
                    for r in rs
                    for t in r["rounds"]
                    if t["round"] == x
                )
                for x in xs
            ]
            ax.plot(xs, ys, marker="o", label=group.replace("_", " "))
        ax.set_title(f"Experiment {section}")
        ax.set_xlabel("After round delivery")
        ax.set_ylim(-0.03, 1.03)
        ax.grid(alpha=0.2)
        ax.legend(fontsize=7, loc="lower right")
    axes[0].set_ylabel("Cumulative citation-linked recipient fraction")
    fig.suptitle(
        "Post-hoc message reach: citations can dispute a claim, not endorse it"
    )
    fig.tight_layout()
    fig.savefig("reports/overnight-experiments/propagation.png", dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("runs/overnight-v1"))
    main(p.parse_args().root)
