# Verified report citations

Checked against the original arXiv records on 8 November 2026. All four are cited as preprints, not as independently verified findings or peer-reviewed publications. Author–date citations in the Word report link to the checked versions; bibliography entries include DOI links.

- Miao et al. (2025), *Response Attack: Exploiting Contextual Priming to Jailbreak Large Language Models*, [arXiv:2507.05248v2](https://arxiv.org/abs/2507.05248v2). Supports the discussion of earlier responses steering later behaviour.
- Wu et al. (2026), *Internal Safety Collapse in Frontier Large Language Models*, [arXiv:2603.23509v1](https://arxiv.org/abs/2603.23509v1). Supports the discussion of task, validator and data requirements.
- Weckbecker et al. (2026), *Thought Virus: Viral Misalignment via Subliminal Prompting in Multi-Agent Systems*, [arXiv:2603.00131v1](https://arxiv.org/abs/2603.00131v1). Supports the discussion of bias propagation between agents.
- Gong et al. (2026), *On Task, Off Track: Benchmarking LLM and Agent Robustness to Near-Target Prompt Injection*, [arXiv:2610.32531v1](https://arxiv.org/abs/2610.32531v1). Supports evaluating answers that remain close to the task but contain incorrect changes.

These papers motivate the study; they do not establish our experiment's outcomes. Figure 2 comes only from [saved run metrics](../runs/oversight-ablation-v1/metrics.json). Its [CSV](figures/results-chart-data.csv) and [provenance](figures/provenance.json) identify the plotted rows. Checks within each evidence condition reuse the same twelve responses. Blocked reports are not repaired tasks. No new inference was performed for this revision.
