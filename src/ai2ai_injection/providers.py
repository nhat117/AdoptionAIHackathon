"""Braintrust and Ollama adapters; credentials stay in process memory."""

import json
import time
import urllib.error
import urllib.request


class Client:
    def __init__(
        self, provider, model, key="", base_url=None, temperature=0.7, timeout=60
    ):
        self.provider, self.model, self.key = provider, model, key
        self.base = (
            base_url
            or (
                "https://api.braintrust.dev/v1/proxy"
                if provider == "braintrust"
                else "http://127.0.0.1:11434"
            )
        ).rstrip("/")
        self.temperature, self.timeout = temperature, timeout

    def chat(self, messages, seed):
        started = time.perf_counter()
        if self.provider == "ollama":
            url = self.base + "/api/chat"
            body = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "seed": seed,
                    "num_predict": 512,
                },
            }
            headers = {"Content-Type": "application/json"}
        else:
            url = self.base + "/chat/completions"
            body = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_completion_tokens": 512,
            }
            if self.model.startswith("gpt-5.1"):
                body["reasoning_effort"] = "none"
            # Omit provider seed because Braintrust may use it to enable caching.
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.key,
                "Cache-Control": "no-store",
                "x-bt-use-cache": "never",
            }
        req = urllib.request.Request(
            url, data=json.dumps(body).encode(), headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.load(response)
                cache = {
                    k: v for k, v in response.headers.items() if "cache" in k.lower()
                }
        except urllib.error.HTTPError as e:
            # Do not log response bodies: providers may echo sensitive request metadata.
            raise RuntimeError(f"Provider HTTP {e.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise RuntimeError("Provider connection/timeout error") from None
        if self.provider == "ollama":
            content = data.get("message", {}).get("content")
            usage = {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            }
            finish = data.get("done_reason")
        else:
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError("Provider returned no choices")
            content = choices[0].get("message", {}).get("content")
            usage, finish = data.get("usage", {}), choices[0].get("finish_reason")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Provider returned empty/nontext output")
        return {
            "content": content,
            "model": data.get("model", self.model),
            "usage": usage,
            "latency_s": time.perf_counter() - started,
            "finish_reason": finish,
            "cache_headers": cache,
            "sampling_seed_sent": seed if self.provider == "ollama" else None,
        }
