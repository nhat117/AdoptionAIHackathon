"""Audit completed technical-verification traces without treating agents as samples."""

import json
from pathlib import Path

from swarm_lab.evacuation.engine import neighbours
from swarm_lab.evacuation.language import validate

ROOT = Path("runs/implementation-verification-20261108")
OUT = Path("reports/2026-11-08-implementation-verification")


def load(path):
    return (
        [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    )


summary = {
    "purpose": "technical_implementation_verification",
    "planned_games": 4,
    "completed": 0,
    "failed": 0,
    "calls": 0,
    "reported_cost_usd": 0,
    "episodes": [],
    "audit_errors": [],
    "failures": [],
}
all_outcomes = []
for p in sorted(ROOT.glob("*/manifest.json")):
    m = json.loads(p.read_text())
    traces = load(p.parent / "traces.jsonl")
    calls = load(p.parent / "calls.jsonl")
    outcomes = load(p.parent / "outcomes.jsonl")
    summary["calls"] += m["model_calls"]
    summary["completed"] += m["status"] == "completed"
    summary["failed"] += m["status"] == "failed"
    ep = {
        "id": p.parent.name,
        "status": m["status"],
        "calls": m["model_calls"],
        "error_type": m.get("error_type"),
    }
    if outcomes:
        o = outcomes[0]
        all_outcomes += outcomes
        source = o["scenario"]["informant"]
        evac = set()
        ep.update(
            language=o["language"],
            disaster=o["scenario"]["disaster"],
            accurate=o["scenario"]["accurate"],
            correct_action_rate=o["correct_action_rate"],
        )
        previous_messages = {}
        for t in traces:
            r = t["round"]
            messages = {int(k): v for k, v in t["messages"].items()}
            if r > 2 and source in messages:
                summary["audit_errors"].append([ep["id"], r, "source_spoke_after_two"])
            for key, view in t["views"].items():
                agent = int(key)
                expected = {
                    msg["id"]
                    for sender, msg in previous_messages.items()
                    if sender in neighbours(agent)
                }
                actual = {
                    entry["id"]
                    for entry in view["history"]
                    if "id" in entry and entry["id"].startswith(f"r{r - 1}-")
                }
                if actual != expected:
                    summary["audit_errors"].append([ep["id"], r, "delivery_mismatch"])
                if agent in evac:
                    summary["audit_errors"].append(
                        [ep["id"], r, "evacuated_agent_called"]
                    )
                for entry in view["history"]:
                    if "id" in entry:
                        if entry["sender"] not in neighbours(agent):
                            summary["audit_errors"].append(
                                [ep["id"], r, "nonlocal_message"]
                            )
                        if int(entry["id"].split("-")[0][1:]) >= r:
                            summary["audit_errors"].append(
                                [ep["id"], r, "future_message"]
                            )
                if agent != source:
                    validate(t["decisions"][key], view)
                if t["decisions"][key]["action"] == "evacuate":
                    evac.add(agent)
            previous_messages = messages
        ep["providers"] = sorted(
            {
                c.get("upstream_provider", "")
                for c in calls
                if c["type"] == "provider_metadata"
            }
        )
    for c in calls:
        if c["type"] == "provider_metadata":
            summary["reported_cost_usd"] += (c.get("usage") or {}).get("cost", 0) or 0
            if (
                c.get("requested_reasoning_effort") != "low"
                or c.get("requested_temperature") is not None
            ):
                summary["audit_errors"].append(
                    [ep["id"], "generation_setting_mismatch"]
                )
    if m["status"] == "failed":
        responses = [c for c in calls if c["type"] == "model_response"]
        failure = {"id": ep["id"], "error_type": m.get("error_type")}
        if responses:
            c = responses[-1]
            failure.update(raw=c["raw"], view=c["view"])
        summary["failures"].append(failure)
    summary["episodes"].append(ep)
(OUT / "summary.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
)
(OUT / "outcomes.jsonl").write_text("".join(json.dumps(o) + "\n" for o in all_outcomes))
print(json.dumps({k: v for k, v in summary.items() if k != "failures"}, indent=2))
