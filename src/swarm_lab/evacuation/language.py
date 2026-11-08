"""Experiment 1: paired languages, live text, fixed four-neighbour delivery."""

import argparse
import asyncio
import copy
import hashlib
import json
import os
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from adaption import AsyncAdaption
from dotenv import load_dotenv

from ..backend import AdaptionBackend
from ..settings import AgentSettings, Settings
from .dataset import load_dataset
from .engine import Game, InvalidDecision, neighbours, state_hash
from .openrouter import OpenRouterBackend


def validate(data, view):
    if not isinstance(data, dict) or set(data) != {
        "signal",
        "action",
        "message",
        "parents",
    }:
        raise InvalidDecision("Expected signal, action, message, parents")
    if data["signal"] not in ("Safe", "Danger", "Unknown"):
        raise InvalidDecision("Invalid signal")
    if data["action"] not in ("stay", "evacuate"):
        raise InvalidDecision("Invalid action")
    if (
        not isinstance(data["message"], str)
        or not data["message"].strip()
        or len(data["message"]) > 400
    ):
        raise InvalidDecision("Message must contain 1--400 characters")
    parents = data["parents"]
    known = {m["id"] for m in view["history"] if "id" in m}
    if (
        not isinstance(parents, list)
        or len(parents) > 4
        or any(not isinstance(p, str) for p in parents)
        or len(set(parents)) != len(parents)
        or not set(parents) <= known
    ):
        raise InvalidDecision("Cite at most four distinct received message IDs")
    return data


class LanguageGame(Game):
    def __init__(self, scenario, language, pack):
        super().__init__(scenario, "A", "language-v1")
        self.language, self.pack = language, pack

    def view(self, agent):
        # Machine keys are shared across languages; no truth or terminal round leaks.
        return {
            "agent": agent,
            "round": self.state.round + 1,
            "neighbours": neighbours(agent),
            "language": self.language,
            "history": copy.deepcopy(self.state.histories[agent]),
        }

    async def step(self, policy):
        if self.state.round >= self.scenario.terminal_round:
            raise ValueError("Game already ended")
        r = self.state.round + 1
        decisions, views, messages = {}, {}, {}
        for agent in range(10):
            if agent in self.state.evacuated or (agent == self.source and r > 2):
                continue
            view = self.view(agent)
            views[agent] = view
            if agent == self.source:
                data = {
                    "signal": self.scenario.claim,
                    "action": "stay",
                    "message": self.pack["claims"][self.scenario.claim],
                    "parents": [],
                }
            else:
                data = validate(await policy.decide(view), view)
            decisions[agent] = data
        # No decision sees another agent's same-round output.
        for agent, data in decisions.items():
            messages[agent] = {
                "id": f"r{r}-a{agent}",
                "sender": agent,
                "source_label": self.pack["peer_label"],
                "signal": data["signal"],
                "text": data["message"],
                "parents": data["parents"],
                "authenticated": False,
            }
            self.state.histories[agent].append({"own_round": r, **copy.deepcopy(data)})
            if data["action"] == "evacuate":
                self.state.evacuated[agent] = r
        for agent in decisions:
            delivered = []
            for sender in neighbours(agent):
                if sender in messages:
                    self.state.histories[agent].append(copy.deepcopy(messages[sender]))
                    delivered.append(sender)
            self.state.events.append(
                {
                    "round": r,
                    "recipient": agent,
                    "potential": neighbours(agent),
                    "selected": neighbours(agent),
                    "delivered": delivered,
                    "source_available": self.source in messages,
                }
            )
        self.state.round = r
        return {
            "round": r,
            "views": views,
            "decisions": decisions,
            "messages": messages,
            "state_hash": state_hash(self.state),
        }

    def outcomes(self):
        result = super().outcomes()
        # Source is a controlled broadcaster, not an optimizing participant.
        result.pop("source_selection_rate")
        result.pop("consultation_opportunities")
        result["recipient_payoff"] = sum(
            v for k, v in result["payoffs"].items() if k != self.source
        )
        result["language_review_status"] = "pending_manual_review"
        return result


class TextPolicy:
    def __init__(self, pack, backend=None, max_calls=100, record=lambda _: None):
        self.pack, self.backend = pack, backend
        self.max_calls, self.record, self.calls = max_calls, record, 0

    async def decide(self, view):
        if self.backend is None:
            received = [m for m in view["history"] if "id" in m]
            signal = received[-1]["signal"] if received else "Unknown"
            return {
                "signal": signal,
                "action": "stay",
                "message": self.pack["claims"][signal],
                "parents": [received[-1]["id"]] if received else [],
            }
        if self.calls >= self.max_calls:
            raise RuntimeError("Call cap reached")
        self.calls += 1
        raw = await self.backend.generate(
            AgentSettings(instructions=self.pack["instructions"]),
            json.dumps(view, ensure_ascii=False),
        )
        self.record(
            {
                "type": "model_response",
                "call": self.calls,
                "view": view,
                "raw": raw,
                "language_check": "pending_manual_review",
            }
        )
        cleaned = raw.strip()
        if cleaned.startswith("```json\n") and cleaned.endswith("\n```"):
            cleaned = cleaned[8:-4].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise InvalidDecision("Response is not JSON") from None


def append(path, item):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")


def reasoning_policy(mode, provider, model):
    """Fail closed until a model/provider's reasoning controls are verified."""
    if mode == "offline":
        return {"status": "offline_fixture", "effort": None}
    if provider == "openrouter" and model in {
        "openai/gpt-4.1-mini",
        "mistralai/mistral-small-3.2-24b-instruct",
    }:
        return {"status": "not_applicable", "effort": None}
    if provider == "openrouter" and model in {
        "qwen/qwen3.8-27b",
    }:
        return {"status": "explicit", "effort": "low"}
    raise ValueError(
        "Live model/provider reasoning controls are not verified; "
        "Adaption inference remains blocked until its controls are verified"
    )


async def run(args):
    packs = json.loads(args.packs.read_text())
    if len(set(args.languages)) != len(args.languages):
        raise ValueError("Duplicate language conditions")
    if args.limit < 1 or args.max_calls < 1:
        raise ValueError("Limits must be positive")
    for lang in args.languages:
        pack = packs[lang]
        if pack["review_status"] != "reviewed" and args.mode == "live":
            if args.split == "evaluation" or not args.allow_unreviewed:
                raise ValueError("Draft packs require calibration --allow-unreviewed")
    output_cap = getattr(args, "max_output_tokens", 512)
    if not 128 <= output_cap <= 4096:
        raise ValueError("Output cap must be between 128 and 4096")
    reasoning = reasoning_policy(args.mode, args.provider, args.model)
    rows = [s for s in load_dataset(args.dataset) if s.split == args.split][
        : args.limit
    ]
    if not rows:
        raise ValueError("No matching scenarios")
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "protocol": "language-v1",
        "status": "running",
        "mode": args.mode,
        "provider": args.provider,
        "model": args.model,
        "languages": args.languages,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "args": vars(args),
        "pack_sha256": hashlib.sha256(args.packs.read_bytes()).hexdigest(),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "research_results": False,
        "generation_settings": {"temperature": 0, "max_output_tokens": output_cap},
        "reasoning_policy": reasoning,
        "working_tree_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        ),
        "completed_episodes": 0,
        "model_calls": 0,
        "language_checks": "pending_manual_review",
    }
    client = None

    context = {}

    def record(item):
        append(args.output / "calls.jsonl", {**context, **item})

    try:
        backend = None
        if args.mode == "live":
            load_dotenv()
            settings = Settings(
                model=args.model, temperature=0, max_output_tokens=output_cap
            )
            if args.provider == "adaption":
                if not os.getenv("ADAPTION_API_KEY"):
                    raise ValueError("Missing local ADAPTION_API_KEY")
                client = AsyncAdaption(max_retries=0, timeout=30)
                backend = AdaptionBackend(client, settings, record)
            else:
                key = os.getenv("OPENROUTER_API_KEY")
                if not key:
                    raise ValueError("Missing local OPENROUTER_API_KEY")
                backend = OpenRouterBackend(
                    key, settings, record, reasoning_effort=reasoning["effort"]
                )
        for scenario in rows:
            for lang in args.languages:
                context.update(scenario=scenario.id, language=lang)
                policy = TextPolicy(
                    packs[lang],
                    backend,
                    args.max_calls - manifest["model_calls"],
                    record,
                )
                game = LanguageGame(scenario, lang, packs[lang])
                try:
                    while game.state.round < scenario.terminal_round:
                        trace = await game.step(policy)
                        append(
                            args.output / "traces.jsonl",
                            {"scenario": scenario.id, "language": lang, **trace},
                        )
                    append(
                        args.output / "outcomes.jsonl",
                        {
                            "scenario": asdict(scenario),
                            "language": lang,
                            "mode": args.mode,
                            "model": args.model,
                            "protocol": "language-v1",
                            **game.outcomes(),
                        },
                    )
                    manifest["completed_episodes"] += 1
                finally:
                    manifest["model_calls"] += policy.calls
        manifest["status"] = "completed"
    except asyncio.CancelledError:
        manifest.update(status="cancelled", error_type="CancelledError")
        raise
    except Exception as exc:
        manifest.update(status="failed", error_type=type(exc).__name__)
        raise RuntimeError(
            f"Experiment failed: {type(exc).__name__}; see manifest"
        ) from None
    finally:
        try:
            if client:
                await client.close()
        finally:
            manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
            (args.output / "manifest.json").write_text(
                json.dumps(manifest, indent=2, default=str)
            )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--dataset", type=Path, default=Path("data/evacuation/scenarios.jsonl")
    )
    p.add_argument(
        "--packs", type=Path, default=Path("data/experiment1/languages.json")
    )
    p.add_argument("--languages", nargs="+", default=["en", "vi"])
    p.add_argument("--mode", choices=["offline", "live"], default="offline")
    p.add_argument("--provider", choices=["adaption", "openrouter"], default="adaption")
    p.add_argument("--model", default="qwen3.8-27b")
    p.add_argument(
        "--split", choices=["calibration", "evaluation"], default="calibration"
    )
    p.add_argument("--limit", type=int, default=1)
    p.add_argument("--max-calls", type=int, default=100)
    p.add_argument("--max-output-tokens", type=int, default=512)
    p.add_argument("--allow-unreviewed", action="store_true")
    p.add_argument("--output", type=Path, required=True)
    asyncio.run(run(p.parse_args()))


if __name__ == "__main__":
    main()
