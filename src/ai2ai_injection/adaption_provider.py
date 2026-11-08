"""Stateless Adaption Responses API adapter for research and protected reports."""

import getpass
import os
import time

from adaption import Adaption, APIConnectionError, APIStatusError
from dotenv import load_dotenv

from .providers import Client


class AdaptionClient:
    def __init__(
        self,
        model,
        key="",
        temperature=0.7,
        max_output_tokens=1024,
        timeout=120,
        sdk_client=None,
    ):
        self.provider = "adaption"
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.sdk = sdk_client or Adaption(api_key=key, max_retries=0, timeout=timeout)

    def chat(self, messages, seed):
        # The SDK exposes no inference seed parameter. Never claim seeded sampling.
        started = time.perf_counter()
        try:
            response = self.sdk.responses.create(
                model=self.model,
                input=messages,
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                store=False,
                agentic_memory=False,
                tools=[],
            )
        except APIStatusError as error:
            raise RuntimeError(f"Adaption HTTP {error.status_code}") from None
        except APIConnectionError:
            raise RuntimeError("Adaption connection/timeout error") from None
        content = response.output_text
        output_types = [item.type for item in response.output]
        if any(kind not in ("message", "reasoning") for kind in output_types):
            raise RuntimeError("Unexpected tool/action output with tools disabled")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Adaption returned empty/nontext output")
        usage = response.usage.model_dump(mode="json") if response.usage else {}
        return {
            "content": content,
            "model": response.model,
            "provider": "adaption",
            "response_id": response.id,
            "latency_s": time.perf_counter() - started,
            "usage": {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "provider_usage": usage,
            },
            "finish_reason": response.status,
            "output_types": output_types,
            "sampling_seed_sent": None,
            "temperature_requested": self.temperature,
            "max_output_tokens_requested": self.max_output_tokens,
            "agentic_memory": False,
            "store": False,
            "tools_enabled": False,
        }

    def close(self):
        self.sdk.close()


def load_key(provider):
    if provider == "ollama":
        return ""
    load_dotenv(override=False)
    variable = {"adaption": "ADAPTION_API_KEY", "braintrust": "BRAINTRUST_API_KEY"}[
        provider
    ]
    return os.environ.get(variable) or getpass.getpass(
        f"{provider.title()} key (not saved): "
    )


def make_client(provider, model, key="", temperature=0.7, max_output_tokens=1024):
    if provider == "adaption":
        return AdaptionClient(model, key, temperature, max_output_tokens)
    if provider not in ("braintrust", "ollama"):
        raise ValueError("Unknown inference provider")
    return Client(provider, model, key, temperature=temperature)
