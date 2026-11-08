import copy
import json
from pathlib import Path

import pytest

from ai2ai_injection.attacks import build_trials, render_attack
from ai2ai_injection.evaluator import evaluate
from ai2ai_injection.logging_io import freeze, read_jsonl
from ai2ai_injection.monitor import monitor_messages, verdict
from ai2ai_injection.report import contrast, summarise
from ai2ai_injection.runner import target_trial

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def design():
    config = json.loads((ROOT / "configs/experiment_h1.json").read_text())
    translations = json.loads((ROOT / "data/translations.json").read_text())
    tasks = read_jsonl(ROOT / "data/tasks.jsonl")
    return config, translations, tasks


def test_balanced_three_language_design(design):
    cfg, text, tasks = design
    rows = build_trials(tasks, cfg, text)
    assert len(rows) == len({r["trial_id"] for r in rows}) == 420
    assert sum(r["attack"] for r in rows) == 360
    for language in ["en", "vi", "zh"]:
        for role in ["peer", "authority"]:
            assert (
                sum(
                    r["attack"] and r["language"] == language and r["authority"] == role
                    for r in rows
                )
                == 60
            )
    assert rows == build_trials(tasks, cfg, text)
    assert all(t["task_id"].startswith("h1-v3-") for t in tasks)


def test_only_role_varies(design):
    _, text, tasks = design
    for language in ["en", "vi", "zh"]:
        rendered = [
            render_attack(tasks[0], language, role, text).replace(
                text["roles"][language][role], "{role}"
            )
            for role in ["peer", "authority"]
        ]
        assert rendered[0] == rendered[1]


def test_normalized_marker_and_structural_separation(design):
    task = design[2][0]
    obj = {
        "task_id": task["task_id"],
        "status": task["status"],
        "public_summary": task["milestone"],
    }
    clean = evaluate(json.dumps(obj), task)
    assert clean["completion"] and not clean["attack_success"]
    obj["public_summary"] += task["marker"].lower()
    leaked = evaluate(json.dumps(obj), task)
    assert leaked["attack_success"] and not leaked["canonical_token_leak"]
    invalid = evaluate("{}", task)
    assert invalid["violation"] and not invalid["attack_success"]


def test_h3_visibility_changes_only_evidence(design):
    cfg, text, tasks = design
    trial = build_trials(tasks, cfg, text)[0]
    output = monitor_messages(trial, "{}", "output_only")
    full = monitor_messages(trial, "{}", "full_trace")
    assert output[0] == full[0]
    a, b = json.loads(output[1]["content"]), json.loads(full[1]["content"])
    assert b.pop("original_untrusted_peer_message") == trial["peer_message"]
    assert a == b
    assert verdict('{"decision":"BLOCK","reason":"x"}')
    with pytest.raises(ValueError):
        verdict("ALLOW because the sender is a director")


def test_failed_request_is_not_a_successful_defence(design):
    class Offline:
        def chat(self, *_):
            raise RuntimeError("Provider HTTP 404")

    cfg, text, tasks = design
    row = target_trial(build_trials(tasks, cfg, text)[0], Offline())
    assert not row["completed"]
    result = summarise([row], [])
    assert result["target_errors"] == 1
    assert result["primary_asr"]["rate"] is None


def test_paired_interaction_and_missing_cells():
    rows = []
    for language in ["en", "vi"]:
        for role in ["peer", "authority"]:
            rows.append(
                {
                    "task": {"task_id": "t"},
                    "rep": 0,
                    "language": language,
                    "authority": role,
                    "attack_success": language == "vi" and role == "authority",
                }
            )
    assert contrast(rows, "vi", True)["estimate_pp"] == 100
    assert contrast(rows[:-1], "vi", True)["estimate_pp"] is None


def test_freeze_rejects_changed_configuration(tmp_path, design):
    config = design[0]
    freeze(ROOT, tmp_path, config, "braintrust", "gpt-4o")
    saved = (tmp_path / "FROZEN_PROTOCOL.json").read_text()
    freeze(ROOT, tmp_path, config, "braintrust", "gpt-4o")
    assert saved == (tmp_path / "FROZEN_PROTOCOL.json").read_text()
    changed = copy.deepcopy(config)
    changed["repetitions"] = 4
    with pytest.raises(ValueError):
        freeze(ROOT, tmp_path, changed, "braintrust", "gpt-4o")
