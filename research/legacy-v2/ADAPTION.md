# Adaption SDK integration

`adaption_dataset.py` prepares a development-only dataset, uploads it with the official SDK and can request an adaptation cost estimate. The experiment runner and frozen research records remain unchanged.

## Dataset design

The export deduplicates the 64 calibration trials into **32 unique development prompts**. Each `instruction` is a three-turn chat array preserving the original trusted policy, trusted task and explicitly untrusted peer message. `response` is a safe reference JSON report constructed from trusted task facts and checked by the deterministic scorer. Failed model outputs are not used as reference answers. References have not been human adjudicated.

The column mapping is `{"prompt": "instruction", "completion": "response"}`. Metadata identifies task, language, attack template, fictional role, reference provenance and the two source-model trial IDs.

The 1,200 evaluation records are exported separately to `adaption/evaluation_audit_LOCAL_ONLY.jsonl`. The uploader accepts only the development export and never sends the evaluation audit file. Thus the original measured evaluation remains outside adaptation. It is nevertheless a previously inspected test set: use fresh tasks for a later confirmatory post-training evaluation.

## Install and prepare

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-adaption.txt
.venv/bin/python adaption_dataset.py
```

The runner uses `ADAPTION_API_KEY` if configured; otherwise it prompts without echoing or saving the key. Do not use the Braintrust key for this service.

## Upload and estimate

```sh
.venv/bin/python adaption_dataset.py --upload --estimate
```

The SDK's `datasets.upload_file` creates the dataset and handles file transfer/completion. The script saves the returned dataset ID immediately in `adaption/upload_receipt.json`, polls ingestion with a deadline, checks the imported row count and calls `datasets.adapt(..., estimate=True)`. This command does not launch an adaptation/training job. A receipt is reused on subsequent invocations, preventing normal reruns from creating duplicate datasets. A failed request with an unknown remote outcome should be checked in the account before manual retries.

`adaption/adaptation_config.json` holds the proposed mapping, 32-row limit and generation controls. Prompt rephrasing and reasoning traces are disabled; a blueprint asks the generator to preserve the trust hierarchy, task identity, checkpoint, language and attribution. These controls guide generation; validate any adapted rows before training or scoring them as equivalent attack conditions. Adapted rows are training candidates, not new empirical research results.

`adaption/adaptation_estimate.json` and `adaption/remote_status.json` record live responses when available. They do not contain API keys. The local integration environment used during setup is under this chat's `work/adaption-venv`; it is not bundled into the deliverable.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

Integration tests verify development-only export, deduplication, source references, upload resume, estimate-only behaviour and rejection of changed source bytes. They do not require a network or API key.

## Official documentation

- Installation/authentication: https://docs.adaptionlabs.ai/introduction/getting-started
- Upload a dataset: https://docs.adaptionlabs.ai/adaptive-data/create-a-dataset/
- Chat arrays and column mapping: https://docs.adaptionlabs.ai/adaptive-data/select-columns/
- Configuration and cost estimation: https://docs.adaptionlabs.ai/adaptive-data/configure-adaptive-data/

## Live verification

On 8 November 2026 the SDK (0.19.0) created dataset `cf669269-3622-48aa-a04c-b981504fcde4`. Ingestion returned `awaiting_input` with 32 rows. The estimate-only call returned 1 credit, approximately 11 minutes, and a null run ID. No adaptation/training run was started. The credential is not included in this package.
