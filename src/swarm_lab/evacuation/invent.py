"""Estimate, launch once, or download Adaption Invent candidate stimuli."""

import argparse
import hashlib
import json
from pathlib import Path

from adaption import Adaption
from dotenv import load_dotenv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["estimate", "launch", "download"])
    parser.add_argument(
        "--prompt", type=Path, default=Path("data/evacuation/invent-prompt.txt")
    )
    parser.add_argument("--rows", type=int, default=12)
    parser.add_argument("--max-credits", type=float, default=2)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    load_dotenv()
    with Adaption(max_retries=0, timeout=60) as client:
        if args.action == "download":
            receipt = json.loads(args.receipt.read_text())
            dataset = client.datasets.get(receipt["id"])
            print("Generation status:", dataset.status)
            if dataset.status != "succeeded":
                return
            if not args.output:
                parser.error("download requires --output")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("xb") as stream:
                stream.write(
                    client.datasets.download(receipt["id"], file_format="jsonl").read()
                )
            print("Downloaded candidates to", args.output)
            return
        prompt = args.prompt.read_text()
        request = dict(
            dataset_prompt=prompt,
            rows=args.rows,
            name="Evacuation message pairs calibration v1",
        )
        estimate = client.datasets.invent(**request, estimate=True)
        print("Estimated credits:", estimate.estimated_credits)
        if args.action == "estimate":
            return
        if (
            estimate.estimated_credits is None
            or estimate.estimated_credits > args.max_credits
        ):
            raise ValueError("Credit estimate exceeds explicit launch cap")
        if args.receipt.exists():
            raise ValueError("Receipt exists; check status, do not create another job")
        digest = hashlib.sha256((prompt + str(args.rows)).encode()).hexdigest()
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(
            json.dumps(
                {
                    "status": "launching",
                    "idempotency_key": "evacuation-v1-" + digest,
                }
            )
        )
        result = client.datasets.invent(
            **request,
            idempotency_key="evacuation-v1-" + digest,
        )
        receipt = result.model_dump()
        receipt["prompt_sha256"] = hashlib.sha256(prompt.encode()).hexdigest()
        args.receipt.write_text(json.dumps(receipt, indent=2, default=str))
        print("Dataset:", result.id, "status:", result.status)


if __name__ == "__main__":
    main()
