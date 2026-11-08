"""Stateless Adaption Responses API adapter for research and protected reports."""

import getpass
import os
import time

from adaption import Adaption, APIConnectionError, APIStatusError
from dotenv import load_dotenv

from .pacing import SHARED_PACER, retry_after_seconds
from .providers import Client


class ResponseOutputError(RuntimeError):
    """A response without usable final text, retaining non-reasoning diagnostics."""

    def __init__(self, message, metadata):
        super().__init__(message)
        self.response_metadata = metadata
        self.request_attempts = metadata["request_attempts"]


class AdaptionClient:
    def __init__(
        self,
        model,
        key="",
        temperature=0.7,
        max_output_tokens=None,
        timeout=120,
        sdk_client=None,
        pacer=None,
        max_rate_limit_retries=2,
    ):
        self.pacer = pacer or SHARED_PACER
        self.max_rate_limit_retries = max_rate_limit_retries
        self.provider = "adaption"
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else (8192 if model.startswith("qwen") else 1024)
        )
        self.sdk = sdk_client or Adaption(api_key=key, max_retries=0, timeout=timeout)

    def chat(self, messages, seed):
        # The SDK exposes no inference seed parameter. Never claim seeded sampling.
        started = time.perf_counter()
        transport_attempts = []
        for attempt in range(self.max_rate_limit_retries + 1):
            self.pacer.wait()
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
                transport_attempts.append(
                    {"attempt": attempt + 1, "status": "response"}
                )
                break
            except APIStatusError as error:
                event = {"attempt": attempt + 1, "http_status": error.status_code}
                transport_attempts.append(event)
                if error.status_code == 429 and attempt < self.max_rate_limit_retries:
                    delay = retry_after_seconds(
                        error.response.headers.get("retry-after")
                    )
                    event["retry_after_s"] = delay
                    self.pacer.defer(delay)
                    continue
                failure = RuntimeError(f"Adaption HTTP {error.status_code}")
                failure.request_attempts = transport_attempts
                raise failure from None
            except APIConnectionError:
                failure = RuntimeError("Adaption connection/timeout error")
                failure.request_attempts = transport_attempts
                raise failure from None
        content = response.output_text
        output_types = [item.type for item in response.output]
        usage = response.usage.model_dump(mode="json") if response.usage else {}
        metadata = {
            "response_id": response.id,
            "model": response.model,
            "status": response.status,
            "output_types": output_types,
            "usage": usage,
            "max_output_tokens_requested": self.max_output_tokens,
            "request_attempts": transport_attempts,
        }
        if any(kind not in ("message", "reasoning") for kind in output_types):
            raise ResponseOutputError(
                "Unexpected tool/action output with tools disabled", metadata
            )
        if not isinstance(content, str) or not content.strip():
            raise ResponseOutputError(
                "Adaption returned empty/nontext output", metadata
            )
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
            "request_attempts": transport_attempts,
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


def make_client(provider, model, key="", temperature=0.7, max_output_tokens=None):
    if provider == "adaption":
        return AdaptionClient(model, key, temperature, max_output_tokens)
    if provider not in ("braintrust", "ollama"):
        raise ValueError("Unknown inference provider")
    return Client(provider, model, key, temperature=temperature)
