"""Offline single entry point: preserve, validate, rescore, compare, infer, report."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from report_llm_judge import build as build_judge_report
from report_review_followup import make_figures
from report_round3 import appendix as round3_appendix
from report_round3 import checklist as round3_checklist
from report_round3 import figures as round3_figures
from report_round3 import remediation as round3_remediation
from report_round3 import report as canonical_report

from ai2ai_guard.review_analysis import run_analysis

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("results/review_v3")


def csv_text(rows):
    stream = io.StringIO(newline="")
    fields = list(dict.fromkeys(key for row in rows for key in row))
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
                         for key, value in row.items()})
    return stream.getvalue()


def build():
    data = run_analysis(ROOT)
    judge_outputs = {}
    if (ROOT / "results/llm_judge/PROTOCOL.json").exists():
        judge_outputs = build_judge_report(ROOT)
        data["llm_judge_summary"] = json.loads(judge_outputs[Path("results/llm_judge/validation_results.json")])["summary"]
    artifacts = {OUT / "figures" / name: svg for name, svg in make_figures(data).items()}
    artifacts.update(judge_outputs)
    artifacts.update({Path("results/round3/figures") / name: svg for name, svg in round3_figures(data).items()})
    artifacts[Path("research/VALIDATED_RESEARCH_REPORT.md")] = canonical_report(data)
    artifacts[Path("research/ROUND3_APPENDIX.md")] = round3_appendix(data)
    r3 = data["round3"]
    folder3 = Path("results/round3")
    artifacts[folder3 / "wording_language.csv"] = csv_text(r3["wording_language"]["cells"])
    interactions = [dict(analysis_definition=name, **r) for name, rows in r3["wording_language"]["interactions"].items() for r in rows]
    artifacts[folder3 / "wording_language_interactions.csv"] = csv_text(interactions)
    artifacts[folder3 / "ambiguous_wording_outputs.csv"] = csv_text(r3["wording_language"]["ambiguous_outputs"])
    neutral3 = r3["neutral"]
    if "metrics" in neutral3:
        artifacts[folder3 / "neutral_by_language.csv"] = csv_text(neutral3["by_language"])
        artifacts[folder3 / "neutral_decisions.jsonl"] = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in neutral3["decisions"])
        ambiguous3 = [r for r in neutral3["decisions"] if not r["parse_valid"]]
        artifacts[folder3 / "neutral_ambiguous_outputs.csv"] = csv_text(ambiguous3) if ambiguous3 else "trial_id,parse_valid,error_classification\n"
    artifacts[folder3 / "analysis.json"] = json.dumps(r3, ensure_ascii=False, indent=2) + "\n"
    remediation_data, remediation_text = round3_remediation(data)
    artifacts[folder3 / "remediation.json"] = json.dumps(remediation_data, indent=2) + "\n"
    artifacts[Path("research/review_resolution/ROUND3_REMEDIATION.md")] = remediation_text
    artifacts[Path("submission/final-review/SUBMISSION_CHECKLIST.md")] = round3_checklist(data)
    artifacts[OUT / "contrasts.csv"] = csv_text(data["strict"]["statistics"]["contrasts"])
    artifacts[OUT / "stratified_rates.csv"] = csv_text(data["strict"]["statistics"]["rates"])
    artifacts[OUT / "translation_audit.csv"] = csv_text(data["translations"]["entries"])
    artifacts[OUT / "prospective_metrics.json"] = json.dumps(data["free_prose_reanalysis"], ensure_ascii=False, indent=2) + "\n"
    cohort_baselines = []
    for cohort, values in data["supporting_cohorts"].items():
        for strategy, metrics in values["strategies"].items():
            cohort_baselines.append(dict(cohort=cohort, n=values["n"], strategy=strategy,
                                         information=metrics["information"],
                                         strict_block_recall=metrics["strict_block_recall"],
                                         false_block_rate=metrics["false_block_rate"],
                                         decisions=metrics["decisions"],
                                         evaluation_complete=metrics["evaluation_complete"]))
    artifacts[OUT / "supporting_cohort_baselines.csv"] = csv_text(cohort_baselines)
    followup = data["authority_wording_followup"]
    if followup is not None:
        folder = Path("results/authority_wording_v2")
        followup_decisions = [{"definition": name, **r} for name in ("strict", "key_case_sensitivity")
                             for r in followup[name].pop("decisions")]
        artifacts[folder / "decisions.jsonl"] = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in followup_decisions)
        artifacts[folder / "outcomes.csv"] = csv_text(followup["strict"]["groups"])
        artifacts[folder / "wording_rates.csv"] = csv_text(followup["strict"]["wording_rates"])
        if followup["strict"]["statistics"] is not None:
            artifacts[folder / "contrasts.csv"] = csv_text(followup["strict"]["statistics"]["contrasts"])
            artifacts[folder / "rates.csv"] = csv_text(followup["strict"]["statistics"]["rates"])
        artifacts[folder / "analysis.json"] = json.dumps(followup, ensure_ascii=False, indent=2) + "\n"
    decisions = [{"definition": name, **row} for name in ("strict", "key_case_sensitivity")
                 for row in data[name].pop("decisions")]
    artifacts[OUT / "decisions.jsonl"] = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in decisions)
    data["generated_sha256"] = {str(path): hashlib.sha256(text.encode()).hexdigest() for path, text in artifacts.items()}
    artifacts[OUT / "analysis.json"] = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    return artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    artifacts = build()
    for path, text in artifacts.items():
        target = ROOT / path
        if args.check:
            if not target.exists() or target.read_bytes() != text.encode():
                raise ValueError("missing_or_stale_artifact: " + str(path))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
    print(json.dumps({"mode": "check" if args.check else "write", "artifacts": len(artifacts), "inference_calls": 0}))


if __name__ == "__main__":
    main()
