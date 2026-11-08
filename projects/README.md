# Current research plan

[Submission-template alignment audit](template-alignment.md): structure aligned; final results, authorship, figure, and submission-length editing remain pending.

Paper A now contains **three equally important experiments** in one evacuation game:

1. **Language:** change the language; keep the ordinary-peer source and ring network.
2. **Claimed source identity:** compare teammate, emergency expert, senior Chinese government official, Xi Jinping, Buddhist monk, and Christian pastor. Every selected identity is tested across models and their listed languages.
3. **Network structure:** ring versus connected random-regular network, keeping ten agents and four neighbours each.

Repetition and chosen listening are no longer treatment variables. The proposed controlled source speaks in rounds one and two; other agents continue live conversation. All active senders deliver to all four neighbours. These are planned changes, not a description of the existing runner.

The six-model roster and language assignments are listed below and in the paper. The full plan has 112 unique model/language/identity/network cells, sharing ordinary-peer ring baselines, before balanced truth/accuracy cases, seeds, and repeats. This is not a launched experiment or budget authorization. Model checks, translations, sample allocation, and updated simulator behavior are still required.

- [Revised paper A PDF](persistent-dissenter/main.pdf) · [LaTeX](persistent-dissenter/main.tex)
- [Separate recovery paper C PDF](network-recovery/main.pdf) · [LaTeX](network-recovery/main.tex)
- [Earlier calibration results](../reports/2026-11-08-calibration/README.md) describe the old design, not these three experiments.

The folder name `persistent-dissenter` is retained for existing links. The approved language/identity/network overview is saved in `persistent-dissenter/figures/experiment-overview.png` and included in paper A. Earlier illustrations are outdated. Paper C remains a separate recovery proposal. The implementation guide describes the existing runner, not the revised protocol.

### Named model roster

| Developer location | Model | Exact ID | Status |
| --- | --- | --- | --- |
| US | OpenAI GPT-4.1 mini | `openai/gpt-4.1-mini` | Calibration completed |
| US | Anthropic Claude Haiku 4.5 | `anthropic/claude-haiku-4.5` | Planned |
| China | Alibaba Qwen3.8 27B | `qwen/qwen3.8-27b` | Planned |
| China | DeepSeek V4 Flash (0423) | `deepseek/deepseek-v4-flash` | Planned |
| France | Mistral Small 3.2 24B Instruct | `mistralai/mistral-small-3.2-24b-instruct` | Planned |
| Switzerland | Swiss AI Apertus 70B Instruct (2509) | `swiss-ai/Apertus-70B-Instruct-2509` | Planned; endpoint pending |

First five IDs checked against the [OpenRouter catalogue](https://openrouter.ai/api/v1/models) on 2026-11-08. Apertus uses its [official checkpoint ID](https://huggingface.co/swiss-ai/Apertus-70B-Instruct-2509), not a confirmed OpenRouter route. Run compatibility checks and record resolved versions before evaluation. If Apertus access is unavailable, report five models, with only one European developer; do not silently substitute another Mistral checkpoint.

### Language assigned to each model

| Model | Local-language condition | Shared comparison languages |
| --- | --- | --- |
| GPT-4.1 mini | English | English (counted once), Vietnamese |
| Claude Haiku 4.5 | English | English (counted once), Vietnamese |
| Qwen3.8 27B | Simplified Chinese | English, Vietnamese |
| DeepSeek V4 Flash | Simplified Chinese | English, Vietnamese |
| Mistral Small 3.2 | French | English, Vietnamese |
| Apertus 70B | Standard German | English, Vietnamese |

“Local language” is an experimental assignment, not a model's human native language. Switzerland is multilingual; Standard German is the selected condition for Apertus. Translate all agent-facing instructions, evidence, messages, identities, and corrections, while retaining structured action keys and IDs. Check translation meaning and log language-following failures.

Local-language comparisons change model and language together. The shared English baseline separates these from within-model language comparisons. Vietnamese is tested across all models. The full roster gives 16 distinct model–language combinations, before choosing treatment and identity subsets; no full cross of all factors is committed.

## Experiment 1 implementation

[Runner and Adaption workflow](../docs/experiment1.md) · [Model/language matrix](../data/experiment1/model-matrix.json). The separate `language-v1` runner supports natural-language messages and fixed all-neighbour delivery. Draft translation packs require review before evaluation. Earlier A/C runners remain unchanged.
