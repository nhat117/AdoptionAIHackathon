"""OpenRouter adapter using standard-library HTTP; no tools or hidden state."""

import asyncio
import json
import urllib.request

from ..settings import AgentSettings, Settings


class OpenRouterBackend:
    def __init__(self, api_key: str, settings: Settings, record):
        self.api_key, self.settings, self.record = api_key, settings, record

    async def generate(self, agent: AgentSettings, input_text: str) -> str:
        return await asyncio.to_thread(self._generate, agent, input_text)

    def _generate(self, agent, input_text):
        # Bound prompt size as well as output tokens and runner call count.
        if len((agent.instructions + input_text).encode()) > 16000:
            raise ValueError("OpenRouter pilot prompt exceeds 16000-byte limit")
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
            }
        )
        choices = result.get("choices", [])
        if not choices or choices[0].get("finish_reason") != "stop":
            raise RuntimeError("OpenRouter response did not finish normally")
        text = choices[0].get("message", {}).get("content")
        if not isinstance(text, str) or not text:
            raise RuntimeError("OpenRouter response has no text")
        return text
