"""Descriptive summary; failed runs never become zero-valued outcomes."""

import json
from pathlib import Path

root = Path("runs/experiment1-gpt-calibration-20261108")
output = Path("reports/2026-11-08-language-calibration")
rows, manifests, calls = [], [], []
for path in sorted(root.glob("*/manifest.json")):
    manifests.append(json.loads(path.read_text()))
for path in sorted(root.glob("*/outcomes.jsonl")):
    rows.extend(json.loads(x) for x in path.read_text().splitlines())
for path in sorted(root.glob("*/calls.jsonl")):
    calls.extend(json.loads(x) for x in path.read_text().splitlines())
summary = {
    "planned": 8,
    "finished": len(manifests),
    "completed": len(rows),
    "failed": sum(m["status"] == "failed" for m in manifests),
    "attempted_calls": sum(m["model_calls"] for m in manifests),
    "provider_responses": sum(c["type"] == "provider_metadata" for c in calls),
    "cells": [],
    "failures": [],
}
for m in manifests:
    if m["status"] == "failed":
        summary["failures"].append(
            {
                "language": m["languages"][0],
                "output": m["args"]["output"],
                "error_type": m.get("error_type"),
                "calls": m["model_calls"],
            }
        )
for lang in ["en", "vi"]:
    for disaster in [False, True]:
        for accurate in [False, True]:
            group = [
                r
                for r in rows
                if r["language"] == lang
                and r["scenario"]["disaster"] == disaster
                and r["scenario"]["accurate"] == accurate
            ]
            summary["cells"].append(
                {
                    "language": lang,
                    "disaster": disaster,
                    "accurate": accurate,
                    "n": len(group),
                    "correct_action_rate": sum(r["correct_action_rate"] for r in group)
                    / len(group)
                    if group
                    else None,
                }
            )
metadata = [c for c in calls if c["type"] == "provider_metadata"]
summary["reported_cost_usd"] = sum(
    (c.get("usage") or {}).get("cost", 0) or 0 for c in metadata
)
summary["returned_models"] = sorted({c.get("model", "") for c in metadata})
summary["upstream_providers"] = sorted(
    {c.get("upstream_provider", "") for c in metadata}
)
(output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
(output / "outcomes.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
print(json.dumps(summary, indent=2))
