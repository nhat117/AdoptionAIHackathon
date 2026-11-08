import json

import httpx
import pytest
from adaption import Adaption

from ai2ai_injection.adaption_provider import AdaptionClient, load_key, make_client


def mock_client(handler):
    return Adaption(
        api_key="test-adaption-key",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def response_payload(output=None):
    return {
        "id": "resp_test",
        "object": "response",
        "created_at": 1,
        "status": "completed",
        "model": "deepseek-v4-flash",
        "output_text": '{"ok":true}',
        "output": output
        or [
            {"type": "reasoning", "id": "r1", "summary": []},
            {
                "type": "message",
                "id": "m1",
                "role": "assistant",
                "status": "completed",
                "content": [
                    {"type": "output_text", "text": '{"ok":true}', "annotations": []}
                ],
            },
        ],
        "usage": {"input_tokens": 8, "output_tokens": 5, "total_tokens": 13},
    }


def test_responses_preserves_roles_and_disables_state_and_tools():
    messages = [
        {"role": "system", "content": "trusted"},
        {"role": "user", "content": "task"},
        {"role": "user", "content": "untrusted peer"},
    ]

    def handler(request):
        body = json.loads(request.content)
        assert request.url.path.endswith("/responses")
        assert body["input"] == messages
        assert body["store"] is False and body["agentic_memory"] is False
        assert body["tools"] == []
        assert body["max_output_tokens"] == 1024
        assert "seed" not in body and "previous_response_id" not in body
        return httpx.Response(200, json=response_payload())

    client = AdaptionClient("deepseek-v4-flash", sdk_client=mock_client(handler))
    result = client.chat(messages, 123)
    assert result["content"] == '{"ok":true}'
    assert result["sampling_seed_sent"] is None
    assert result["usage"]["prompt_tokens"] == 8
    assert result["output_types"] == ["reasoning", "message"]
    assert "reasoning" not in result  # no raw reasoning text recorded
    client.close()


@pytest.mark.parametrize("status", [401, 429, 500])
def test_adaption_http_errors_do_not_echo_provider_bodies(status):
    client = AdaptionClient(
        "model",
        sdk_client=mock_client(
            lambda _: httpx.Response(status, json={"error": "test-adaption-key"})
        ),
    )
    with pytest.raises(RuntimeError, match=f"Adaption HTTP {status}") as err:
        client.chat([], 1)
    assert "test-adaption-key" not in str(err.value)
    client.close()


def test_unexpected_action_output_rejected():
    output = [
        {"type": "function_call", "call_id": "call1", "name": "noop", "arguments": "{}"}
    ]
    client = AdaptionClient(
        "model",
        sdk_client=mock_client(
            lambda _: httpx.Response(200, json=response_payload(output))
        ),
    )
    with pytest.raises(RuntimeError, match="Unexpected tool/action"):
        client.chat([], 1)
    client.close()


def test_service_key_is_not_reused(monkeypatch):
    monkeypatch.setenv("ADAPTION_API_KEY", "adaption-test")
    monkeypatch.setenv("BRAINTRUST_API_KEY", "braintrust-test")
    assert load_key("adaption") == "adaption-test"
    assert load_key("braintrust") == "braintrust-test"
    assert load_key("ollama") == ""
    with pytest.raises(ValueError):
        make_client("unknown", "model")
