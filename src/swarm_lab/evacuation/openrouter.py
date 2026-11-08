"""OpenRouter adapter using standard-library HTTP; no tools or hidden state."""

import asyncio
import json
import urllib.request

from ..settings import AgentSettings, Settings


class OpenRouterBackend:
    def __init__(
        self,
        api_key: str,
        settings: Settings,
        record,
        reasoning_effort=None,
        max_prompt_bytes=16000,
    ):
        self.api_key, self.settings, self.record = api_key, settings, record
        self.reasoning_effort = reasoning_effort
        self.max_prompt_bytes = max_prompt_bytes

    async def generate(self, agent: AgentSettings, input_text: str) -> str:
        return await asyncio.to_thread(self._generate, agent, input_text)

    def _generate(self, agent, input_text):
        # Bound prompt size as well as output tokens and runner call count.
        if len((agent.instructions + input_text).encode()) > self.max_prompt_bytes:
            raise ValueError(
                f"OpenRouter prompt exceeds {self.max_prompt_bytes}-byte limit"
            )
        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": agent.instructions},
                {"role": "user", "content": input_text},
            ],
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_output_tokens,
            "provider": {"allow_fallbacks": False, "require_parameters": True},
        }
        # These reasoning endpoints do not expose temperature control.
        if self.settings.model in {
            "openai/gpt-6.1-terra",
            "anthropic/claude-sonnet-5.5",
        }:
            payload.pop("temperature")
        if self.reasoning_effort is not None:
            payload["reasoning"] = {"effort": self.reasoning_effort}
        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
        self.record(
            {
                "type": "provider_metadata",
                "provider": "openrouter",
                "response_id": result.get("id"),
                "model": result.get("model"),
                "upstream_provider": result.get("provider"),
                "usage": result.get("usage"),
                "requested_reasoning_effort": self.reasoning_effort,
                "requested_temperature": payload.get("temperature"),
                "finish_reason": (result.get("choices") or [{}])[0].get(
                    "finish_reason"
                ),
            }
        )
        choices = result.get("choices", [])
        if not choices or choices[0].get("finish_reason") != "stop":
            raise RuntimeError(
                "OpenRouter response did not finish normally; "
                "inspect finish_reason and usage"
            )
        text = choices[0].get("message", {}).get("content")
        if not isinstance(text, str) or not text:
            raise RuntimeError("OpenRouter response has no text")
        return text
