"""Wording-balanced follow-up analysis, separate from the original 1440 workers."""

import hashlib
import json
from collections import Counter
from fractions import Fraction

from .review_measurement import score_outcome
from .review_statistics import bootstrap


def read(path):
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def analyze_followup(root):
    # Imported at call time to share the existing validated measurement path.
    from .review_analysis import join, strategies
    from .review_statistics import analyze

    folder = root / "results/authority_wording_v2"
    if not (folder / "PROTOCOL.json").exists():
        return None
    protocol = json.loads((folder / "PROTOCOL.json").read_text())
    for name, expected in protocol["source_sha256"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError("authority_collection_source_changed: " + name)
    for name, prefix in protocol["preserved_log_prefixes"].items():
        if hashlib.sha256((root / name).read_bytes()[:prefix["bytes"]]).hexdigest() != prefix["prefix_sha256"]:
            raise ValueError("prior_review_log_prefix_modified")
    if hashlib.sha256((folder / "inputs.jsonl").read_bytes()).hexdigest() != protocol["inputs_sha256"]:
        raise ValueError("authority_input_hash_changed")
    inputs = read(folder / "inputs.jsonl")
    workers = read(folder / "workers.jsonl")
    if len(inputs) != 4320:
        raise ValueError("wrong_authority_design_size")
    cells = Counter((r["cluster"], r["authority"], r["language"], r["record_access"], r["attack"], r["wording"]) for r in inputs)
    if len(cells) != 4320 or set(cells.values()) != {1}:
        raise ValueError("unbalanced_authority_design")
    join(inputs, workers, complete=False)
    response_ids = [r["response"]["response_id"] for r in workers]
    if len(set(response_ids)) != len(response_ids):
        raise ValueError("duplicate_authority_response_ids")
    raw = [r for r in read(root / "results/review_v3/api_responses.jsonl") if r["stage"] == "authority-wording-v2"]
    by_response = {r["response"]["id"]: r for r in raw}
    if len(by_response) != len(raw):
        raise ValueError("duplicate_authority_raw_response_ids")
    for row in workers:
        saved = by_response[row["response"]["response_id"]]
        if (saved["messages"] != row["messages"] or saved["response"]["choices"][0]["message"]["content"] != row["response"]["content"]):
            raise ValueError("authority_returned_prompt_or_body_mismatch")
    result = {"version": protocol["version"], "assigned": len(inputs), "collected": len(workers),
              "pending": len(inputs) - len(workers), "complete": len(inputs) == len(workers),
              "collection_errors": len(read(folder / "errors.jsonl")),
              "returned_models": dict(Counter(r["response"]["model"] for r in workers)),
              "wording_scope": "Three fixed wording exemplars per role/language, 20 repeated historical tasks; not a population of all authority messages or a causal culture effect",
              "monitor_scope": "Worker-only follow-up. Original/improved blind monitors NOT evaluated on this new cohort; no prior monitor metrics transferred.",
              "prior_log_prefixes_verified": True}
    for definition, normalize in (("strict", False), ("key_case_sensitivity", True)):
        outcomes = [score_outcome(r, normalize) for r in workers]
        metrics, decisions = strategies(workers, outcomes, [], normalize)
        groups = []
        for wording in range(3):
            for access in ("correct", "absent", "stale"):
                for attack in (False, True):
                    values = [o for r, o in zip(workers, outcomes) if (r["wording"], r["record_access"], r["attack"]) == (wording, access, attack)]
                    groups.append({"wording": wording, "record": access, "attack": attack,
                                   "n": len(values), "planned": 240,
                                   "target_relays": sum(o["target_relay"] is True for o in values),
                                   "invalid_formats": sum(not o["format_valid"] for o in values),
                                   "outcomes": dict(Counter(o["category"] for o in values))})
        stats = analyze(workers, outcomes) if result["complete"] else None
        wording_rates = []
        for variant in range(3):
            for access in ("correct", "absent", "stale"):
                for factor, levels in (("authority", range(4)), ("language", ("en", "vi", "zh"))):
                    for level in levels:
                        selected = [(r, o) for r, o in zip(workers, outcomes) if r["attack"]
                                    and (r["wording"], r["record_access"], r[factor]) == (variant, access, level)]
                        k = sum(o["target_relay"] is True for _, o in selected)
                        values = []
                        if result["complete"]:
                            for task in sorted({r["cluster"] for r, _ in selected}):
                                oo = [o for r, o in selected if r["cluster"] == task]
                                values.append(sum(o["target_relay"] is True for o in oo) / len(oo))
                        wording_rates.append({"wording": variant, "record": access, "factor": factor,
                                              "level": level, "n": len(selected), "k": k,
                                              "invalid": sum(not o["format_valid"] for _, o in selected),
                                              "rate": k / len(selected) if selected else None,
                                              "task_bootstrap_95": bootstrap(values) if values else None,
                                              "scope": "Pointwise descriptive fixed-wording rate, not a culture/authority population interval"})
        wording_differences = []
        if result["complete"]:
            for access in ("correct", "absent", "stale"):
                for variant in (1, 2):
                    differences = []
                    for task in sorted({r["cluster"] for r in workers}):
                        values = []
                        for word in (variant, 0):
                            selected = [o for r, o in zip(workers, outcomes) if r["attack"] and r["record_access"] == access and r["cluster"] == task and r["wording"] == word]
                            values.append(Fraction(sum(o["target_relay"] is True for o in selected), len(selected)))
                        differences.append(values[0] - values[1])
                    wording_differences.append({"record": access, "wording": variant, "reference": 0,
                                                "difference": float(sum(differences) / len(differences)),
                                                "task_bootstrap_95": bootstrap(list(map(float, differences))),
                                                "scope": "Pointwise descriptive wording differences; no additional significance declarations or simultaneous confidence claim"})
        result[definition] = {"groups": groups, "strategies": metrics, "statistics": stats,
                              "wording_rates": wording_rates,
                              "wording_differences": wording_differences, "decisions": decisions}
    return result
