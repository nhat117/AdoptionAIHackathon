"""Upload synthetic rows to Adaption; no adaptation/training is launched."""

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from adaption import Adaption
from dotenv import load_dotenv

from .dataset import load_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset", type=Path, default=Path("data/evacuation/scenarios.jsonl")
    )
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    rows = load_dataset(args.dataset)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    # Leave a marker even on uncertain failure; never silently repeat an upload.
    with args.receipt.open("x") as stream:
        json.dump(
            {
                "status": "started",
                "sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
            },
            stream,
        )
    export = args.receipt.with_suffix(".upload.jsonl")
    with export.open("x") as stream:
        for row in rows:
            stream.write(
                json.dumps(
                    {
                        "prompt": json.dumps(
                            {
                                "purpose": "simulator configuration only",
                                "scenario": asdict(row),
                            },
                            sort_keys=True,
                        ),
                        "completion": json.dumps(
                            {
                                "oracle_state": row.truth,
                                "oracle_action": "evacuate" if row.disaster else "stay",
                            }
                        ),
                    }
                )
                + "\n"
            )
    load_dotenv()
    with Adaption(max_retries=0, timeout=60) as client:
        result = client.datasets.upload_file(
            export,
            name="Evacuation pilot scenarios v1",
            processing_mode="raw",
            column_mapping={"prompt": "prompt", "completion": "completion"},
        )
        receipt = {
            "dataset_id": result.dataset_id,
            "status": "uploaded",
            "rows": len(load_dataset(args.dataset)),
            "sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        }
        args.receipt.write_text(json.dumps(receipt, indent=2))
        print(json.dumps(receipt))
        status = client.datasets.get_status(result.dataset_id)
        receipt["ingestion_status"] = status.status
        receipt["ingested_rows"] = status.row_count
        args.receipt.write_text(json.dumps(receipt, indent=2))
        print("Ingestion:", status.status, "rows:", status.row_count)


if __name__ == "__main__":
    main()
