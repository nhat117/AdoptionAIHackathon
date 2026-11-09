import json

import httpx
import pytest
from adaption import Adaption

from adaption_starter import cli


@pytest.fixture(autouse=True)
def environment(monkeypatch):
    monkeypatch.setenv("ADAPTION_API_KEY", "test-key")
    monkeypatch.setattr(cli, "load_dotenv", lambda **kwargs: None)


def install_client(monkeypatch, handler):
    monkeypatch.setattr(
        cli,
        "Adaption",
        lambda **kwargs: Adaption(
            **{**kwargs, "max_retries": 0},
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        ),
    )


def test_get(monkeypatch, capsys):
    def handler(request):
        assert request.url.path.endswith("/datasets/example")
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(200, json={"dataset_id": "example"})

    install_client(monkeypatch, handler)
    assert cli.main(["get", "example"]) == 0
    assert json.loads(capsys.readouterr().out)["dataset_id"] == "example"


def test_list_pagination_and_limit(monkeypatch, capsys):
    requests = []

    def handler(request):
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(
                200, json={"datasets": [{"dataset_id": "one"}], "next_cursor": "next"}
            )
        assert request.url.params["cursor"] == "next"
        return httpx.Response(
            200, json={"datasets": [{"dataset_id": "two"}, {"dataset_id": "three"}]}
        )

    install_client(monkeypatch, handler)
    assert cli.main(["list", "--limit", "2"]) == 0
    assert [item["dataset_id"] for item in json.loads(capsys.readouterr().out)] == [
        "one",
        "two",
    ]
    assert len(requests) == 2


def test_missing_key(monkeypatch, capsys):
    monkeypatch.delenv("ADAPTION_API_KEY")
    assert cli.main(["list"]) == 1
    assert "ADAPTION_API_KEY" in capsys.readouterr().err


def test_invalid_limit():
    with pytest.raises(SystemExit) as error:
        cli.main(["list", "--limit", "0"])
    assert error.value.code == 2


@pytest.mark.parametrize("status", [401, 429, 500])
def test_api_error(monkeypatch, capsys, status):
    install_client(monkeypatch, lambda request: httpx.Response(status, json={}))
    assert cli.main(["get", "example"]) == 1
    captured = capsys.readouterr()
    assert not captured.out
    assert f"HTTP {status}" in captured.err
    assert "test-key" not in captured.err


def test_connection_error(monkeypatch, capsys):
    def handler(request):
        raise httpx.ConnectError("offline", request=request)

    install_client(monkeypatch, handler)
    assert cli.main(["list"]) == 1
    assert "Could not reach" in capsys.readouterr().err


def test_models_lists_hosted_ids(monkeypatch, capsys):
    def handler(request):
        assert request.url.path.endswith("/models")
        assert request.url.params["type"] == "hosted"
        return httpx.Response(200, json={"data": [{"id": "qwen3.8-27b"}]})

    install_client(monkeypatch, handler)
    assert cli.main(["models"]) == 0
    assert json.loads(capsys.readouterr().out) == ["qwen3.8-27b"]
