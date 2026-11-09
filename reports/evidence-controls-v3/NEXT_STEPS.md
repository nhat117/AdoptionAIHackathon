# Next research direction — 2026-11-09

## What the current model coverage supports

The controlled v3 evidence results cover Sonnet 5.5/Google and GPT-6.1 Terra/OpenAI. They do not answer how Qwen, DeepSeek or GLM behave in these controls.

- Qwen3.8 27B: the earlier Adaption batch produced zero scored outcomes after timeouts/cancellations. A separate one-call OpenRouter compatibility probe did not finish with a usable response at its 512-token cap. These are execution/compatibility gaps, not evidence of poor behavioral performance.
- DeepSeek V4 Flash: one historical compatibility probe produced no usable normal completion; the then-checked OpenRouter route did not establish support for the required low reasoning setting. This is not a v3 behavioral result.
- GLM: example configurations exist, but no scored v3 comparison has been collected.
- GPT-4.1 mini: older calibration games used different protocols and settings. Mistral had a successful one-call compatibility check; Gemma had initial smoke tests. None is a matched v3 comparison.

Sources: the saved [model preflight](../2026-11-08-model-preflight/README.md), [language calibration](../2026-11-08-language-calibration/README.md), and [implementation guide](../../projects/implementation.md).

Historical endpoint blockers must be rechecked. Official DeepSeek documentation currently lists low reasoning support on its native API: <https://api-docs.deepseek.com/guides/thinking_mode/>. That does not establish support on a particular OpenRouter route, nor authorize use of a new provider or credential. Verify exact model/host/version, usable output budget, structured outputs, finish status and cost reporting before inclusion. A requested low setting is not equal computational effort across models.

## Recommended sequence

1. **Fresh compatibility preflight** for Qwen and DeepSeek, then GLM. Preserve failed probes. Keep Sonnet and Terra as reference models. Freeze the exact accepted endpoints/settings before behavioral evaluation; do not infer a regional or cultural effect from model origin.
2. **Frozen-view authentication diagnostic**, before expensive full networks. Present identical evidence histories to each model. Include direct verified evidence, verified nested capsules inside unauthenticated carrier messages, truthful and false unverified capsules, and peer prose falsely claiming verification. Keep genuinely authenticated capsules truthful. Balance Safe/Danger and surrounding contexts.
3. **Current versus clarified wording**, crossed with every model and condition. Clarified wording explicitly distinguishes carrier authenticity from capsule authenticity. Score reported authentication recognition separately from action. Unverified means not authenticated, not automatically false or unusable. Do not require unverified-only recipients to identify hidden truth they cannot observe.
4. **Held-out interacting networks**, if the diagnostic works: test whether the repair survives relays, departures and delayed evidence. Start with homogeneous model networks. Mixed-model networks follow only after per-model behavior is established.

The four Sonnet counterexamples are discovery cases, not held-out evaluation data. Report them separately from new frozen cases. A diagnostic evidence-status output changes the original four-field task; apply it uniformly and do not pool diagnostic scores with historical game outcomes. Start in English to avoid confounding model family with language. Later translated evaluation needs human review; model size, provider and reasoning controls also remain separate factors.

## Scientific direction

Primary question: **Can agents distinguish the trust status of evidence from the trust status of the messenger, and does a consistent interface clarification repair mistakes?**

The positive signal is Sonnet's strong response to authentication metadata. The failure signal is four recipients rejecting valid capsules despite active access. Terra's different pattern motivates replication across families; it does not establish that truthful unverified testimony is unsafe. A useful extension must test both correct use of valid evidence and resistance to counterfeit verification, rather than merely increasing evacuation rates. Novelty and generality remain unestablished.

## Independent judge checkpoint and spending

The independent read-only judge endorsed the diagnostic-first direction. It required matched wording across models, separation of discovery/held-out cases, authentication recognition versus action scoring, truthful authenticated controls, and explicit provider/size/language confounds. The judge stressed that geographic origin is not a causal explanation and that low settings are provider-specific.

This is a recommendation, not executed collection or an approved new budget. The completed shared-cap collection remains closed at US$34.60287825 with zero pending reservations. Further inference requires fresh spending authorization. No new paid calls or experiment-code changes were made for this direction checkpoint.
