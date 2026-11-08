"""Read datasets through the official Adaption SDK."""

import argparse
import json
import os
import sys
from typing import Optional, Sequence

from adaption import Adaption, APIConnectionError, APIStatusError
from dotenv import load_dotenv


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="List datasets as JSON")
    listing.add_argument(
        "--limit", type=int, default=20, help="Maximum results (default: 20)"
    )
    commands.add_parser("models", help="List hosted inference model IDs")
    getting = commands.add_parser("get", help="Get a dataset as JSON")
    getting.add_argument("dataset_id")
    args = parser.parse_args(argv)
    if args.command == "list" and args.limit < 1:
        parser.error("--limit must be positive")

    # Explicit environment variables take precedence over the local .env file.
    load_dotenv(override=False)
    api_key = os.environ.get("ADAPTION_API_KEY", "").strip()
    if not api_key:
        print("Set ADAPTION_API_KEY in your environment or .env file.", file=sys.stderr)
        return 1

    try:
        with Adaption(api_key=api_key, timeout=30.0, max_retries=2) as client:
            if args.command == "models":
                print(
                    json.dumps(
                        [m.id for m in client.models.list(type="hosted").data], indent=2
                    )
                )
            elif args.command == "get":
                print(client.datasets.get(args.dataset_id).to_json())
            else:
                results = []
                for dataset in client.datasets.list():
                    results.append(dataset.to_dict())
                    if len(results) >= args.limit:
                        break
                print(json.dumps(results, indent=2))
    except APIConnectionError:
        print(
            "Could not reach Adaption. Check your connection and retry.",
            file=sys.stderr,
        )
        return 1
    except APIStatusError as error:
        print(f"Adaption request failed (HTTP {error.status_code}).", file=sys.stderr)
        return 1
    return 0
