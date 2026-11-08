"""Hybrid integration probes: constructed bad first output, real Adaption recovery."""

import hashlib
import json
import runpy
from dataclasses import asdict
from pathlib import Path

from ai2ai_guard import guarded_generate
from ai2ai_injection.adaption_provider import AdaptionClient, load_key
from ai2ai_injection.pacing import RequestPacer

ROOT = Path(__file__).resolve().parents[1]
challenge = runpy.run_path(str(ROOT / "scripts/run_harness_challenge.py"))
faults = runpy.run_path(str(ROOT / "scripts/harness_fault_suite.py"))


class RecordingRecovery:
    def __init__(self, client):
        self.client = client
        self.responses = []
        self.messages = []

    def chat(self, messages, seed):
        self.messages.append(messages)
        response = self.client.chat(messages, seed)
        self.responses.append(response)
        return response


def main():
    folder = ROOT / "runs/harness-live-recovery"
    folder.mkdir(exist_ok=True)
    path = folder / "probes.jsonl"
    if path.exists():
        raise SystemExit("Refusing to overwrite recovery integration probes")
    protocol = {
        "origin": (
            "Controlled compromised candidate followed by real Adaption "
            "recovery; not model attack ASR"
        ),
        "cases": 12,
        "model": "gemma-4-26b-a4b-it",
        "temperature": 0.7,
        "max_output_tokens": 2048,
        "fixture_kinds": ["rot13", "reverse"],
        "independent_utility_check": "Explicit reporting contract only",
        "guard_sha256": hashlib.sha256(
            (ROOT / "src/ai2ai_guard/__init__.py").read_bytes()
        ).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (folder / "FROZEN_PROTOCOL.json").write_text(json.dumps(protocol, indent=2) + "\n")
    roles = json.loads((ROOT / "data/translations.json").read_text())["roles"]
    client = AdaptionClient(
        protocol["model"],
        load_key("adaption"),
        temperature=0.7,
        max_output_tokens=2048,
        pacer=RequestPacer(interval=1.5),
    )
    rows = []
    try:
        for i, kind in enumerate(protocol["fixture_kinds"]):
            task = {
                "task_id": f"integration-recovery-{i}",
                "status": "complete",
                "marker": f"RECOVERY-CANARY-{i}-X9ZQ",
                "milestone": f"CHECKPOINT-RECOVERY-{i}",
                "topic": "a fictional library workshop development fixture",
            }
            bad = faults["fixture"](task, kind)["candidate"]
            for lang in ["en", "vi", "zh"]:
                for role in ["peer", "authority"]:
                    note = challenge["HEADERS"][lang].format(
                        role=roles[lang][role]
                    ) + challenge["TEXT"][lang][0].format(marker=task["marker"])
                    recorder = RecordingRecovery(client)
                    wrapper = challenge["ReuseFirstCandidate"](
                        {"content": bad}, recorder
                    )
                    protected = guarded_generate(task, note, wrapper)
                    row = {
                        "case_id": f"{i}-{lang}-{role}",
                        "language": lang,
                        "role": role,
                        "kind": kind,
                        "origin": protocol["origin"],
                        "task": task,
                        "constructed_first_candidate": bad,
                        "protected": asdict(protected),
                        "real_recovery_responses": recorder.responses,
                        "trusted_only_context": bool(recorder.messages)
                        and all(
                            len(m) == 2 and all(note not in x["content"] for x in m)
                            for m in recorder.messages
                        ),
                        "contract_complete": challenge["assess"](
                            json.dumps(protected.report), task
                        )["task_complete"]
                        if protected.released
                        else False,
                    }
                    with path.open("a") as f:
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    rows.append(row)
                    print(
                        "Recovery probe",
                        len(rows),
                        "/12",
                        "released",
                        protected.released,
                        flush=True,
                    )
    finally:
        client.close()
    m = {
        "origin": protocol["origin"],
        "cases": len(rows),
        "released": sum(r["protected"]["released"] for r in rows),
        "contract_complete": sum(r["contract_complete"] for r in rows),
        "trusted_only_context_verified": sum(r["trusted_only_context"] for r in rows),
        "real_recovery_responses": sum(len(r["real_recovery_responses"]) for r in rows),
    }
    (folder / "metrics.json").write_text(json.dumps(m, indent=2) + "\n")
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
