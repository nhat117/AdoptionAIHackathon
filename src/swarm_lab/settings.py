"""Small editable settings; graph topology stays visible in graph.py."""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AgentSettings:
    instructions: str = "Respond to the supplied task."
    offline_output: str = "Placeholder response (offline; no model was called)."


@dataclass(frozen=True)
class Settings:
    model: str = "qwen3.5-397b"
    temperature: float = 0.0
    max_output_tokens: int = 256
    branch_a: AgentSettings = field(default_factory=AgentSettings)
    branch_b: AgentSettings = field(default_factory=AgentSettings)

    @classmethod
    def load(cls, path: Path) -> "Settings":
        data = json.loads(path.read_text(encoding="utf-8"))
        # Dataclass constructors reject misspelled/unknown settings.
        for key in ("branch_a", "branch_b"):
            if key in data:
                data[key] = AgentSettings(**data[key])
        settings = cls(**data)
        if not isinstance(settings.model, str) or not settings.model.strip():
            raise ValueError("model must be a nonempty string")
        if not 0 <= settings.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if (
            isinstance(settings.max_output_tokens, bool)
            or not isinstance(settings.max_output_tokens, int)
            or settings.max_output_tokens < 1
        ):
            raise ValueError("max_output_tokens must be a positive integer")
        for agent in (settings.branch_a, settings.branch_b):
            if not isinstance(agent.instructions, str) or not isinstance(
                agent.offline_output, str
            ):
                raise ValueError(
                    "agent instructions and offline_output must be strings"
                )
        return settings
