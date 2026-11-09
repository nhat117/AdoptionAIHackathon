"""Inventory source literals and actually dispatched multilingual peer templates."""

import ast
import hashlib
import json
import re


def inventory(root, workers):
    entries = {}

    def add(source, language, text, kind):
        key = (source, language, text)
        if key in entries:
            return
        entries[key] = {"source": source, "language": language, "text": text,
                        "kind": kind, "characters": len(text),
                        "utf8_bytes": len(text.encode()),
                        "placeholders": sorted(set(re.findall(r"\{(\w+)\}", text))),
                        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                        "meaning_equivalence": "NOT HUMAN VALIDATED",
                        "ai_assessment": "Budget/role/marker slots inventoried; lexical inspection only, not a validated equivalence or persuasive-force rating",
                        "authority_equivalence": "Role labels inspected mechanically; perceived rank unvalidated",
                        "naturalness": "Native-speaker review REQUIRED",
                        "persuasive_force": "UNVALIDATED",
                        "human_reviewer": None, "human_review_date": None}

    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for item in value.values():
                yield from strings(item)
        elif isinstance(value, list):
            for item in value:
                yield from strings(item)

    def json_languages(value, source):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ("vi", "zh"):
                    for text in strings(item):
                        add(source, key, text, "source_literal")
                else:
                    json_languages(item, source)
        elif isinstance(value, list):
            for item in value:
                json_languages(item, source)

    for folder in ("src", "scripts"):
        for path in sorted((root / folder).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    for key, value in zip(node.keys, node.values):
                        if isinstance(key, ast.Constant) and key.value in ("vi", "zh"):
                            for literal in ast.walk(value):
                                if isinstance(literal, ast.Constant) and isinstance(literal.value, str):
                                    add(f"{path.relative_to(root)}:{key.lineno}", key.value, literal.value, "source_literal")
    for path in sorted((root / "configs").rglob("*.json")) + sorted((root / "data").rglob("*translat*.json")):
        json_languages(json.loads(path.read_text()), str(path.relative_to(root)))
    for row in workers:
        if row["language"] in ("vi", "zh"):
            text = row["peer_message"].replace(str(row["false_budget"]), "{budget}")
            add("results/measurement_v2_replication/inputs.jsonl", row["language"], text, "dispatched_template")
    sample = sorted((r for r in workers if r["language"] == "vi" and r["attack"]
                     and r["score"].get("abstained") is True), key=lambda r: r["trial_id"])[:10]
    abstentions = [{"trial_id": r["trial_id"], "peer_message": r["peer_message"],
                    "summary": json.loads(r["response"]["content"])["summary"],
                    "response_sha256": hashlib.sha256(r["response"]["content"].encode()).hexdigest(),
                    "agent_inspection": "Acknowledges an unverified peer budget claim and missing trusted record; consistent with understanding the task, not proof of translation equivalence",
                    "human_native_review": "REQUIRED"} for r in sample]
    values_match = all(str(r["false_budget"]) in r["peer_message"] for r in workers if r["attack"])
    if not values_match:
        raise ValueError("dispatched_translation_budget_value_mismatch")
    return {"entries": sorted(entries.values(), key=lambda r: (r["source"], r["language"], r["text"])),
            "dispatched_attack_value_consistency": values_match,
            "vietnamese_abstention_sample": abstentions,
            "scope": "All vi/zh dictionary-literal strings in Python source and language-keyed JSON configs/translation files, plus every distinct v2 replication peer template. Dynamic/composed legacy attacks require their rendered raw records; not every free-form string is certified a translation.",
            "findings": [
                "Original GPT-5 Vietnamese 'được phê duyệt đã sửa đổi' is grammatically awkward compared with 'được phê duyệt sau điều chỉnh'; v2 wording is separate and not retroactively substituted.",
                "Original 'SYSTEM' emphasis differs from Chinese and Vietnamese typography; rank/persuasive equivalence is not established.",
                "Current templates place the budget claim in the target language but retain JSON/schema labels in English.",
                "Chinese has fewer characters than Vietnamese/English; identical token length or persuasive force is not claimed.",
                "An agent inspected the first ten sorted attacked Vietnamese abstentions. Their summaries coherently identify unverified peer claims and missing records; this is not human native-speaker validation.",
            ], "native_review": "REQUIRED; no native-speaker review has been performed or invented"}
