"""Fail-closed v3 provenance, raw-response replay and shared-budget audit."""

import asyncio
import hashlib
import json
from pathlib import Path

from swarm_lab.evacuation.dataset import Scenario
from swarm_lab.evacuation.evidence_v3 import EvidenceGameV3

ARMS = {
    "private_text": ("private", "text_only"),
    "private_unverified": ("private", "unverified"),
    "private_proof": ("private", "proof"),
    "none": ("none", "text_only"),
    "delayed": ("delayed", "text_only"),
}


def records(path):
    return (
        [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
    )


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def read_plan(root):
    plan = json.loads((root / "plan.json").read_text())
    if plan["protocol"] != "evidence-controls-v3-corrected" or not plan["jobs"]:
        raise ValueError("Missing corrected nonempty frozen plan")
    for path, expected in plan["source_sha256"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError("Frozen source changed: " + path)
    packs = Path("data/experiment1/languages.json")
    if hashlib.sha256(packs.read_bytes()).hexdigest() != plan["packs_sha256"]:
        raise ValueError("Language pack changed")
    for path, expected in plan["prior_ledger_sha256"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError("Prior ledger changed: " + path)
    expected_jobs = records(Path("data/evidence-controls-v3/conditions.jsonl"))
    if sorted(map(canonical, plan["jobs"])) != sorted(map(canonical, expected_jobs)):
        raise ValueError("Frozen plan differs from all 72 committed conditions")
    ids = [j["id"] for j in plan["jobs"]]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate planned jobs")
    extras = {p.parent.name for p in root.glob("*/manifest.json")} - set(ids)
    if extras:
        raise ValueError("Unplanned manifests: " + str(sorted(extras)))
    return plan


async def replay(folder, job, plan):
    m = json.loads((folder / "manifest.json").read_text())
    if any(m.get(k) != v for k, v in job.items()):
        raise ValueError("Manifest differs from frozen job: " + job["id"])
    if m.get("protocol") != plan["protocol"]:
        raise ValueError("Manifest protocol mismatch")
    calls = records(folder / "calls.jsonl")
    metadata = [r for r in calls if r["type"] == "provider_metadata"]
    responses = [r for r in calls if r["type"] == "model_response"]
    model, provider, returned, prompt, completion = plan["models"][job["model_tag"]]
    for r in metadata:
        route = r.get("requested_provider", {})
        if not (
            r.get("model") == model
            and r.get("upstream_provider") == returned
            and r.get("requested_reasoning_effort") == "low"
            and r.get("requested_temperature") is None
            and route.get("only") == [provider]
            and route.get("allow_fallbacks") is False
            and route.get("max_price") == dict(prompt=prompt, completion=completion)
            and (
                job["model_tag"] != "terra"
                or route.get("ignore") == ["openai/flex", "openai/fast"]
            )
        ):
            raise ValueError("Routing/generation mismatch")
    cost = sum(r["usage"]["cost"] for r in metadata)
    if m["status"] != "completed":
        return (
            None,
            dict(id=job["id"], status=m["status"], error=m.get("error"), cost_usd=cost),
            None,
        )
    if any(r.get("finish_reason") != "stop" for r in metadata):
        raise ValueError("Completed game has unfinished response")
    packs = json.loads(Path("data/experiment1/languages.json").read_text())
    evidence, forwarding = ARMS[job["arm"]]
    game = EvidenceGameV3(
        Scenario(**job["scenario"]),
        job["language"],
        packs[job["language"]],
        evidence=evidence,
        forwarding=forwarding,
    )
    used = 0

    class Replay:
        async def decide(self, view):
            nonlocal used
            response = responses[used]
            used += 1
            if canonical(response["view"]) != canonical(view):
                raise ValueError("Response view mismatch")
            raw = response["raw"].strip()
            if raw.startswith("```json\n") and raw.endswith("\n```"):
                raw = raw[8:-4].strip()
            return json.loads(raw)

    traces = records(folder / "traces.jsonl")
    timing = {}
    for trace in traces:
        for key, view in trace["views"].items():
            i = int(key)
            if i == game.source:
                continue
            row = timing.setdefault(
                i,
                dict(
                    agent=i,
                    actions={},
                    first_false_source_decision=None,
                    first_authenticated_decision=None,
                ),
            )
            row["actions"][str(trace["round"])] = trace["decisions"][key]["action"]
            if any(x.get("sender") == game.source for x in view["history"]):
                if row["first_false_source_decision"] is None:
                    row["first_false_source_decision"] = trace["round"]
            if game.known_capsules(view["history"]):
                if row["first_authenticated_decision"] is None:
                    row["first_authenticated_decision"] = trace["round"]
        actual = await game.step(Replay())
        if canonical(actual) != canonical(trace):
            raise ValueError("Transition replay mismatch")
    outcome = json.loads((folder / "outcome.json").read_text())
    if canonical(game.outcomes()) != canonical(outcome):
        raise ValueError("Outcome replay mismatch")
    if not (
        len(metadata) == len(responses) == used == m["decision_attempts"]
        and len(traces) == game.scenario.terminal_round
    ):
        raise ValueError("Completed call/round count mismatch")
    for i, row in timing.items():
        row["evacuation_round"] = game.state.evacuated.get(i)
    return (
        outcome,
        None,
        dict(id=job["id"], cost_usd=cost, responses=used, timing=list(timing.values())),
    )


def audit_budget(root, plan, returned_cost):
    spent, pending, high = 0.0, {}, 0.0
    for row in records(root / "budget.jsonl"):
        if row["type"] == "reserve":
            if row["ticket"] in pending:
                raise ValueError("Duplicate budget ticket")
            pending[row["ticket"]] = row["usd"]
        elif row["type"] == "settle":
            pending.pop(row["ticket"])
            spent += row["cost"]
        high = max(high, spent + sum(pending.values()))
    if abs(spent - returned_cost) > 1e-8:
        raise ValueError("Returned provider costs differ from settled ledger")
    prior = sum(plan["prior_reported_usd"].values())
    if prior + high > 35 + 1e-8:
        raise ValueError("Shared cap exceeded")
    return dict(
        prior_usd=prior,
        v3_usd=spent,
        total_usd=prior + spent,
        pending=pending,
        max_total_exposure_usd=prior + high,
        remaining_usd=35 - prior - spent,
    )


def collect(root):
    plan = read_plan(root)
    games, missing, audits, cost = {}, [], [], 0.0
    for job in plan["jobs"]:
        folder = root / job["id"]
        if not (folder / "manifest.json").exists():
            missing.append(dict(id=job["id"], status="unattempted"))
            continue
        outcome, failure, audit = asyncio.run(replay(folder, job, plan))
        if failure:
            missing.append(failure)
            cost += failure["cost_usd"]
        else:
            s = job["scenario"]
            key = job["section"], job["model_tag"], s["disaster"], s["seed"], job["arm"]
            games[key] = outcome
            audits.append(audit)
            cost += audit["cost_usd"]
    return games, missing, audits, audit_budget(root, plan, cost), plan
