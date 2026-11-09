"""Run authorized initial judging/revisions, then rebuild truthful offline outputs."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Required for all paid stages")
    parser.add_argument("--cap-usd", type=float)
    args = parser.parse_args()
    if not args.run:
        subprocess.run([sys.executable, "scripts/run_full_gpt5_judge.py"], cwd=ROOT, check=True)
        return
    if args.cap_usd is None or not 0 < args.cap_usd <= 650:
        parser.error("Explicit authorized --cap-usd required, at most 650 cumulative")
    command = [sys.executable, "scripts/run_full_gpt5_judge.py", "--cap-usd", str(args.cap_usd), "--workers", "8"]
    outcomes = []
    initial = subprocess.run(command + ["--run"], cwd=ROOT)
    outcomes.append({"stage": "initial", "exit_code": initial.returncode})
    status_path = ROOT / "results/llm_judge_gpt5/execution_status.json"
    status = json.loads(status_path.read_text()) if status_path.exists() else {}
    if initial.returncode == 0 and status.get("valid_initial_judgments") == 5760:
        revision = subprocess.run(command + ["--revisions"], cwd=ROOT)
        outcomes.append({"stage": "revisions", "exit_code": revision.returncode})
    else:
        outcomes.append({"stage": "revisions", "status": "NOT_STARTED_INITIAL_VALIDATION_INCOMPLETE"})
    # The collectors are now stopped. Never rebuild analysis against mutating evidence.
    for script in ("scripts/run_research_pipeline.py", "scripts/export_review_report.py"):
        result = subprocess.run([sys.executable, script], cwd=ROOT)
        outcomes.append({"stage": script, "exit_code": result.returncode})
        if result.returncode:
            break
    path = ROOT / "results/llm_judge_gpt5/COMPLETION_WORKFLOW.json"
    path.write_text(json.dumps({"stages": outcomes, "author_edits_confirmed": False,
                                "human_proofreading_claimed": False,
                                "official_submission_confirmed": False}, indent=2) + "\n")
    print(json.dumps({"completion_workflow": outcomes}), flush=True)
    if any(row.get("exit_code", 0) != 0 for row in outcomes):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
