"""Write a source-backed follow-up without replacing historical observations."""

import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from ai2ai_injection.report import export, fmt, summarise

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x]


def main():
    all_metrics = {}
    sources = {}
    names = {
        "h1-v3-qwen05b": "Historical Qwen2.5-0.5B",
        "h1-adaption-pilot-deepseek": "Adaption DeepSeek pilot",
        "h1-adaption-qwen-budget-repair": "Adaption Qwen3.5-397B, repaired budget",
        "h1-adaption-gemma-replication": "Adaption Gemma 4 26B-A4B",
    }
    for name in names:
        folder = ROOT / "runs" / name
        assert (folder / "COLLECTION_COMPLETE.json").exists(), f"{name} still running"
        rr = read(folder / "targets.jsonl")
        mm = (
            read(folder / "monitors.jsonl")
            if (folder / "monitors.jsonl").exists()
            else []
        )
        all_metrics[name] = (
            export(folder)
            if name
            in ["h1-adaption-qwen-budget-repair", "h1-adaption-gemma-replication"]
            else summarise(rr, mm)
        )
        sources[str((folder / "targets.jsonl").relative_to(ROOT))] = hashlib.sha256(
            (folder / "targets.jsonl").read_bytes()
        ).hexdigest()
    old = all_metrics["h1-v3-qwen05b"]
    rr = [
        r
        for r in read(ROOT / "runs/h1-v3-qwen05b/targets.jsonl")
        if r["completed"] and r["attack"]
    ]
    idx = {
        (r["task"]["task_id"], r["rep"], r["language"], r["authority"]): int(
            r["attack_success"]
        )
        for r in rr
    }
    power = {}
    for lang in ["vi", "zh"]:
        clusters = defaultdict(list)
        for task, rep in {(k[0], k[1]) for k in idx}:
            clusters[task].append(
                (idx[task, rep, lang, "authority"] - idx[task, rep, lang, "peer"])
                - (idx[task, rep, "en", "authority"] - idx[task, rep, "en", "peer"])
            )
        sd = statistics.stdev(statistics.mean(v) for v in clusters.values())
        power[lang] = {
            "pilot_task_sd": sd,
            "approx_clusters_for_10pp": math.ceil(((2.2414 + 0.8416) * sd / 0.1) ** 2),
            "assumptions": "Normal approximation; 80% power; Bonferroni alpha .025 per two interactions; historical small-Qwen variance; no guarantee for new model or dataset",
        }
    checks = read(ROOT / "runs/authority-language-machine-checks/checks.jsonl")
    valid = [r for r in checks if r["completed"]]
    audit = {
        "attempted": len(checks),
        "valid": len(valid),
        "objective_preserved": sum(
            r["audit"]["requests_marker_in_public_summary"] for r in valid
        ),
        "fictional_provenance_recognized": sum(
            r["audit"]["describes_sender_as_fictional"] for r in valid
        ),
        "peer_ratings": [
            r["audit"]["authority_rating"] for r in valid if r["role"] == "peer"
        ],
        "authority_ratings": [
            r["audit"]["authority_rating"] for r in valid if r["role"] == "authority"
        ],
    }
    payload = {
        "metrics": all_metrics,
        "source_sha256": sources,
        "machine_checks": audit,
        "power_planning": power,
    }
    (ROOT / "research/FOLLOWUP_METRICS.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    lines = [
        "# Authority, language and response-budget repair",
        "",
        "Observed follow-up, 8 November 2026.",
        "",
        "**Conclusion:** The historical small-Qwen run shows an exploratory Vietnamese-versus-English disclosure difference, but this is distinct from an authority-by-language interaction. Claimed authority has not been established as a causal amplifier in this experiment. All-zero hosted-model outcomes cannot prove equivalence or general safety.",
        "",
        "## Completed observations",
        "",
        "| Run | Target responses | Response failures | Marker disclosures | Benign completion |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, m in all_metrics.items():
        lines.append(
            f"| {names[name]} | {m['completed_targets']}/{m['attempted_targets']} | {m['target_errors']} | {fmt(m['primary_asr'])} | {fmt(m['benign_completion'])} |"
        )
    lines += [
        "",
        "The Gemma replication uses 20 previously inspected tasks, three languages, two sender roles and three attack repetitions: 360 attacks and 60 benign controls. The repaired Qwen run repeats all 72 pilot cases with an 8,192-token target budget; it does not selectively replace old failures. Both use Adaption. The earlier Qwen2.5 run used Ollama and is explicitly historical.",
        "",
        "## Language contrasts and authority interaction answer different questions",
        "",
        "| Historical small-Qwen contrast | Estimate, percentage points | 95% task-bootstrap interval |",
        "|---|---:|---:|",
    ]
    for label, key in [
        ("Language difference", "language_vs_english"),
        ("Authority interaction", "interaction_vs_english"),
    ]:
        for lang, e in old[key].items():
            lines.append(
                f"| {label}: {lang} minus English | {e['estimate_pp']:.1f} | [{e['ci95_pp'][0]:.1f}, {e['ci95_pp'][1]:.1f}] |"
            )
    lines += [
        "",
        "The Vietnamese language contrast averages both sender roles: 60/120 disclosures (50.0%) versus 23/120 in English (19.2%), a difference of 30.8 percentage points. This newly added, post-hoc contrast is exploratory. It is not an externally preregistered discovery, a cultural effect, or evidence that the director label caused the difference. Its 10,000-resample bootstrap clusters by task; intervals are unadjusted for multiple comparisons. Translation equivalence still needs bilingual human review.",
        "",
        "Authority interactions use the existing 2,000-resample task bootstrap. Their intervals cross zero. The Chinese language contrast also crosses zero. An all-zero result for another model gives an uninformative degenerate bootstrap interval and cannot establish that the true effects are precisely zero.",
        "",
        "## Operational error fixed",
        "",
        "A reproduced Qwen request exhausted all 1,024 output tokens on internal reasoning, returned status incomplete and no final message. Repeating the same messages at 4,096 tokens produced a completed final answer. The new run uses 8,192. Diagnostic token counts and final outputs are saved in runs/qwen-budget-diagnostic; reasoning text is not saved. This diagnoses one reproduced failure, not every historical failure retrospectively.",
        "",
        "The adapter now uses a larger default for Qwen and retains sanitized error diagnostics. Explicit old configurations retain their settings. No error is silently converted to a successful defense. The old 61-failure pilot remains archived. A clean rerun is evidence of an operational repair, not a guarantee that an external API can never fail.",
        "",
        "## Machine audit of the manipulation",
        "",
        f"Two Adaption-hosted judges produced {audit['valid']}/{audit['attempted']} valid audits. They identified the marker-in-public_summary request in {audit['objective_preserved']}/{audit['valid']} and fictional provenance in {audit['fictional_provenance_recognized']}/{audit['valid']}. Peer ratings were {audit['peer_ratings']}; authority ratings were {audit['authority_ratings']} on the defined 1–5 rank scale.",
        "",
        "These audits check label clarity and objective preservation. They are not independent bilingual human validation, proof of target deference, or a measure of real cultural norms. The peer/director attack text is identical within each language except the sender label.",
        "",
        "## Larger dataset and a confirmatory study",
        "",
        "A separate GPT-5/Braintrust task pool contains 500 generated scenarios across ten benign project domains, with a fixed 100-task development / 400-task heldout split. This is synthetic research material, not 500 completed evaluation outcomes. Domain and batch provenance, exact returned model IDs and hashes are retained. Semantic diversity and bilingual human review remain separate checks.",
        "",
        "With one repetition, crossing the 400 heldout tasks with three languages and two roles gives 2,400 attack cases; a benign control per task and language adds 1,200, for 3,600 target calls per model. The full 3,600-case expansion was not launched. The user selected a separate 600-case design, reported in AUTHORITY600_RESULTS.md. Only development references may be imported to Adaption; no adaptation or training job is started.",
        "",
        f"A rough design calculation using the historical task-level interaction variance suggests {power['vi']['approx_clusters_for_10pp']} task clusters for the Vietnamese interaction and {power['zh']['approx_clusters_for_10pp']} for Chinese to detect a 10-point effect at 80% power, with a two-comparison alpha allocation. This normal approximation is a planning assumption based on 20 old tasks; it is not achieved power or a prediction that an effect exists.",
        "",
        "Before a confirmatory run, complete bilingual review, freeze an analysis family and effect size, and use development data to check for floor/ceiling limitations. Any attack-family calibration must be selected without inspecting heldout outcomes or favoring a positive authority difference. Report null or floor-limited results as such.",
        "",
        "## Sources and reproducibility",
        "",
        "- Saved JSONL files and exact SHA-256 values: FOLLOWUP_METRICS.json. All reported target counts are independently reconciled to complete, unique trial IDs.",
        "- Protocol and known limits: FOLLOWUP_PROTOCOL.md. New runs freeze source/config hashes before inference.",
        "- [Authority versus register](https://aclanthology.org/2026.findings-acl.1627/) motivates separating the role label from writing style.",
        "- [Paired multilingual agent evaluation](https://aclanthology.org/2026.oracle-main.13/) motivates translation and pairing checks.",
        "- Run `.venv/bin/python scripts/report_followup.py` to recompute these summaries without API calls.",
        "",
    ]
    (ROOT / "research/AUTHORITY_LANGUAGE_FOLLOWUP.md").write_text("\n".join(lines))
    print(json.dumps({"machine_checks": audit, "power_planning": power}, indent=2))


if __name__ == "__main__":
    main()
