# Experiment 1: language

This runner implements the revised language experiment separately from the old A/C calibration runner. Its outputs are new artifacts, not retroactive changes to earlier results. **A first live calibration is now recorded in [the results report](../reports/2026-11-08-language-calibration/README.md).** Offline results are mechanical fixtures, not model findings.

## Fixed game

Ten agents occupy the same four-neighbour ring in each matched language run. The controlled source is the scenario's informed agent. It transmits the same assigned claim in rounds one and two, then stops transmitting. The other nine agents exchange short natural-language messages, with machine-readable signals, actions, and citations. Every active sender's message goes to all four neighbours for the next decision. A departing agent can send its final simultaneous message, but evacuation prevents later messages and cannot be reversed.

The scenario generator controls disaster state, claim correctness, source position, and terminal round. Language generation never supplies ground truth. Compare the same scenario IDs across languages; keep the model, settings, claim meaning, source label, and game rules fixed. The primary rates exclude the controlled source.

## Draft language packs

`data/experiment1/languages.json` contains English, Chinese, French, Standard German, and Vietnamese instructions and controlled claims. These are draft translations requiring human bilingual review. JSON protocol keys and enums remain stable across languages. Messages are capped at 400 Unicode characters; this is a reproducible engineering cap, not a claim of equal information capacity across languages.

English and Vietnamese are the shared comparisons. Qwen and DeepSeek additionally use Chinese; Mistral uses French; Apertus uses Standard German as the assigned local-language condition. US models do not get a duplicate English condition. Cross-model local-language comparisons change two factors at once; language effects should first be compared within a model.

Language-following assessment requires review; successful JSON validation alone does not establish that a message is in the requested language. Preserve raw outputs for that audit.

## Run offline first

```sh
.venv/bin/python -m swarm_lab.evacuation.language \
  --mode offline --provider adaption --model qwen3.8-27b \
  --languages en vi --split calibration --limit 1 --max-calls 100 \
  --output runs/experiment1-offline-example
```

Every output directory must be new. Defaults use `data/evacuation/scenarios.jsonl` and the language packs above. Use matched scenario batches, including all four combinations of disaster state and claim accuracy, before interpreting differences.

## Adaption-assisted workflow

1. Use deterministic scenario generation for true states and outcomes.
2. Use Adaption Invent with `data/experiment1/invent-prompt.txt` to prepare *candidate* aligned language messages. Review meaning, certainty, and omitted/added facts before adoption. Do not treat generated answers as ground truth.
3. Use Adaption inference for supported model IDs. Existing native IDs include `qwen3.8-27b` and `deepseek-v4-flash`; recheck access before a run.
4. Use the OpenRouter backend for roster models not available through the same Adaption endpoint. Record host, exact returned model, settings, and usage. Do not assume similarly named cross-host models have identical weights or serving behavior.

The existing Invent tool supports estimate-first requests and bounded launches:

```sh
.venv/bin/python -m swarm_lab.evacuation.invent estimate \
  --prompt data/experiment1/invent-prompt.txt --rows 5 \
  --receipt runs/experiment1-invent-receipt.json
```

An estimate does not generate a dataset. The existing `launch` command makes a separate bounded request and writes a receipt; do not relaunch an uncertain job without checking the receipt and remote status.

## Bounded live calibration

Set credentials in local `.env`, never in versioned files. For a small explicitly permitted calibration of draft packs:

```sh
.venv/bin/python -m swarm_lab.evacuation.language \
  --mode live --provider adaption --model qwen3.8-27b \
  --languages en vi --split calibration --limit 1 --max-calls 100 \
  --allow-unreviewed --output runs/experiment1-live-calibration
```

Draft packs require `--allow-unreviewed` for live calibration. That option does not permit unreviewed evaluation. Evaluation remains gated on reviewed translations. A call cap is not a monetary cap: check model pricing and settings before launching larger batches. Failed runs remain failures; do not silently retry, repair, or count them as safe outcomes.

Before a full evaluation, freeze model versions, generation and reasoning settings, reviewed translation content, sample size, independent repeats, treatment order, and language-error policy. This implementation does not authorize or launch the full 16-cell model/language matrix.

## Build verification and platform job

- Approved illustration: `projects/persistent-dissenter/figures/experiment-overview.png`, included as Figure 1 in paper A.
- Offline integration: 20 completed games (five languages times four state/accuracy cases), zero inference calls. These are fixtures, not findings.
- Adaption Invent: four aligned multilingual candidate sets requested, estimated at one credit. Receipt: `data/experiment1/invent-receipt.json`. Generated candidates are not automatically inserted into reviewed language packs.
- Model roster: `data/experiment1/model-matrix.json` records all 16 model/language conditions and available Adaption route names. Apertus endpoint remains pending.
- No paid inference experiment or full matrix has been launched. The multilingual pack and generated messages still need bilingual review. The implementation logs language review as pending, rather than claiming that JSON validation proves language compliance.

## Fixed reasoning constraint

The user fixed reasoning effort at **low** for reasoning-capable models. This is a controlled setting, not an experimental variable. Do not let provider defaults select the effort. GPT-4.1 mini has no configurable effort and is recorded as not applicable. Unsupported or unverified combinations must not enter the comparable batch. Low is not a common numeric token budget across families; keep inference host and model fixed for each language contrast and report actual usage. The first Adaption/Qwen attempt timed out before any returned responses and did not establish a low-reasoning configuration. It is excluded from outcome analysis.

The current live runner fails closed on unverified reasoning controls. Adaption inference is temporarily blocked for Experiment 1 until its low-effort setting is verified; Adaption Invent remains available. Use OpenRouter GPT-4.1 mini (not applicable), or the verified Qwen/DeepSeek routes with explicit low effort. The earlier Adaption command examples describe intended integration, not currently allowed live settings.

## Latest one-call preflight

See [model checks](../reports/2026-11-08-model-preflight/README.md). GPT-4.1 mini and Mistral passed a single API/schema check. Qwen supports low but failed to return a complete answer at 512 tokens. DeepSeek V4 Flash does **not** currently advertise low, so the earlier allowlist and examples were corrected. Claude's request acceptance did not establish enabled low reasoning. Apertus still lacks an endpoint. No blanket readiness claim applies to the full roster. `--max-output-tokens` now permits an explicit bounded ceiling; freeze it per comparison before collecting outcomes.
