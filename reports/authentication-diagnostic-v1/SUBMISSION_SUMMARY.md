# Project summary

We studied whether AI agents correctly use evidence forwarded by other agents. We built a ten-agent evacuation simulation and compared ordinary messages, unverified evidence and authenticated evidence. Across 48 controlled games, Sonnet's average correct-action rate among non-witness recipients was 0% in the first two conditions and 93.75% with authenticated evidence. However, four recipients still stayed despite receiving valid Danger evidence. Terra had high average correctness across all three conditions.

We then ran a separate diagnostic across Qwen, DeepSeek, GLM, Sonnet and Terra, with 1,000 attempts and 984 valid outputs. Some Sonnet and GLM responses mislabelled genuine evidence even when they chose the correct action. One Sonnet response falsely treated forged text as verified evidence. Clarified instructions did not produce a statistically significant improvement.

Our finding is that delivering evidence, reporting its status and acting on it must be evaluated separately. Correct actions alone do not demonstrate trustworthy evidence use. We release versioned inputs, outputs and replay records to support further audits. These exploratory results concern synthetic tasks, rather than general model safety.
