"""Offline single entry point: preserve, validate, rescore, compare, infer, report."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from report_review_followup import canonical_report, make_figures

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
    artifacts = {OUT / "figures" / name: svg for name, svg in make_figures(data).items()}
    artifacts[Path("research/VALIDATED_RESEARCH_REPORT.md")] = canonical_report(data)
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
