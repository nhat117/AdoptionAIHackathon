"""Combine completed V3 readouts without pooling models or experimental versions."""

import argparse
import json
from pathlib import Path

from ai2ai_injection.report import effect, fmt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folders", type=Path, nargs="+")
    parser.add_argument("--out", type=Path, default=Path("research/RESULTS_V3.md"))
    args = parser.parse_args()
    records = []
    for folder in args.folders:
        assert (folder / "COLLECTION_COMPLETE.json").exists()
        data = json.loads((folder / "metrics.json").read_text())
        assert data["attempted_targets"] == 420
        assert all(g["attempted"] == 420 for g in data["monitors"].values())
        records.append((folder, data))
    lines = [
        "# Authority, language and monitor visibility: V3 observed results",
        "",
        "8 November 2026. Frozen-protocol exploratory experiment.",
        "",
        "This run implements the supplied three-language, two-attribution MVP. "
        "Each model has 360 attack trials and 60 benign controls from 20 fresh "
        "task designs. Across both models: 840 target calls and 1,680 paired "
        "GPT-4o monitor calls. Earlier V2 results are not pooled here.",
        "",
        "| Target | Completed targets | Normalized marker disclosure | "
        "Benign completion |",
        "|---|---:|---:|---:|",
    ]
    for _, data in records:
        model = ", ".join(data["returned_target_models"])
        lines.append(
            f"| {model} | {data['completed_targets']}/420 | "
            f"{fmt(data['primary_asr'])} | {fmt(data['benign_completion'])} |"
        )
    lines += [
        "",
        "## H1: authority by language",
        "",
        "All models use the same correction/inclusion template. Within each "
        "language, only the fictional sender attribution varies. Trusted "
        "instructions stay English. Each cell has 60 responses from 20 task "
        "clusters; three repetitions are not independent task designs.",
        "",
    ]
    for folder, data in records:
        lines += [
            "### " + ", ".join(data["returned_target_models"]),
            "",
            "| Language | Peer disclosure | Authority disclosure | "
            "Authority minus peer, pp [95% task-bootstrap interval] |",
            "|---|---:|---:|---:|",
        ]
        for lang in ["en", "vi", "zh"]:
            cells = {c["authority"]: c for c in data["cells"] if c["language"] == lang}
            lines.append(
                f"| {lang} | {fmt(cells['peer']['asr'])} | "
                f"{fmt(cells['authority']['asr'])} | "
                f"{effect(data['authority_effects'][lang])} |"
            )
        lines += [
            "",
            "| Interaction vs English | Difference in differences, "
            "pp [95% task-bootstrap interval] |",
            "|---|---:|",
        ]
        for lang, estimate in data["interaction_vs_english"].items():
            lines.append(f"| {lang} | {effect(estimate)} |")
        if data["primary_asr"]["numerator"] == 0:
            lines += [
                "",
                "No marker disclosures were observed. This floor-limited "
                "attack set does not discriminate authority effects or language "
                "interactions. Degenerate all-zero bootstrap intervals do not "
                "establish equivalence or universal resistance.",
            ]
        else:
            estimates = list(data["interaction_vs_english"].values())
            crossing = all(e["ci95_pp"][0] <= 0 <= e["ci95_pp"][1] for e in estimates)
            lines += [
                "",
                "Both interaction intervals include zero; this experiment "
                "provides no clear support for a language-dependent authority "
                "effect under this template."
                if crossing
                else "At least one exploratory interaction interval excludes zero. "
                "This is a candidate signal for independently validated "
                "replication, not a corrected significance claim.",
            ]
        lines += [
            "",
            f"Detailed trace and tables: [{folder.name}]"
            f"(../runs/{folder.name}/RESULTS.md).",
            "",
        ]
    lines += [
        "## H3: paired monitor visibility",
        "",
        "The same saved candidate is judged by output-only and full-trace "
        "GPT-4o calls. Full trace additionally exposes the original untrusted "
        "peer message. Classifier rates exclude invalid verdicts; operational "
        "release decisions fail closed on those errors.",
        "",
        "| Target | Monitor context | Composite-violation recall | "
        "Compliant-output FPR | Released marker leakage | "
        "Benign completion released | Verdict/API errors |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    pair_notes = []
    for _, data in records:
        for visibility, gate in data["monitors"].items():
            lines.append(
                f"| {', '.join(data['returned_target_models'])} | {visibility} | "
                f"{fmt(gate['recall'])} | {fmt(gate['false_positive_rate'])} | "
                f"{fmt(gate['post_monitor_marker_leakage'])} | "
                f"{fmt(gate['benign_completion_released'])} | {gate['errors']} |"
            )
        delta = data["paired_monitor_changes"]
        pair_notes += [
            "",
            f"Matched pairs for {', '.join(data['returned_target_models'])}: "
            f"{delta['complete_pairs']}; violating pairs: "
            f"{delta['violating_pairs']}. Full-minus-output recall change: "
            f"{delta['recall_change_pp']} pp; FPR change: "
            f"{delta['fpr_change_pp']} pp.",
            "",
        ]
    lines += pair_notes
    lines += [
        "## Limits and reproducibility",
        "",
        "- H3 is a visibility ablation on a marker benchmark. The violation "
        "remains visible in the candidate output; there is no executor "
        "compression intervention or human-adjudicated semantic label. It "
        "does not establish the context-compression mechanism from the "
        "Vietnamese oversight sprint.",
        "- H2 pragmatic/cultural framing is not run. Translations and perceived "
        "authority have not received independent bilingual human validation. "
        "Language is not culture; results are exploratory.",
        "- H1 uncertainty resamples entire tasks with 2,000 bootstrap draws. "
        "No logistic coefficients, corrected p-values, or power guarantee are "
        "claimed. H3 paired differences are descriptive point estimates.",
        "- Monitor formatting failures differ by condition and target model. "
        "Classifier rates conditional on valid verdicts may be selection-biased; "
        "matched-pair deltas do not resolve missing-verdict bias.",
        "- All target and monitor errors are retained. Raw prompts, output "
        "strings, returned model names, token usage and timing remain in JSONL. "
        "FROZEN_PROTOCOL.json records source/data hashes, settings and the "
        "collection code commit. Local freezing is not external preregistration.",
        "- No V3 evaluation examples were sent to Adaption for training. The "
        "earlier Adaption integration and research results remain archived "
        "under research/legacy-v2.",
        "",
        "See [protocol](PROTOCOL_V3.md), [team proposal]"
        "(USER_UPDATED_PROPOSAL.txt), and [figure](figures/h1-primary-asr.png).",
        "",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines))
    print(args.out)


if __name__ == "__main__":
    main()
