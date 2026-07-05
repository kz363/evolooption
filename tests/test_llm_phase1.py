import json
import urllib.error

import pytest

from evolooption.cli.setup import main
from evolooption.llm.client import StructuredOutputError
from evolooption.llm.config import LLMConfig
from evolooption.llm.ollama import OllamaClient
from evolooption.llm.openai_compatible import OpenAICompatibleClient
from evolooption.llm.roles import RoleRegistry


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps(self.payload).encode()


def test_setup_cli_writes_config(tmp_path) -> None:
    config_path = tmp_path / "llm.json"

    assert main([
        "--config",
        str(config_path),
        "--provider",
        "ollama",
        "--role",
        "analysis=qwen3:8b",
    ]) == 0

    config = LLMConfig.load(config_path)

    assert config.provider == "ollama"
    assert config.roles == {"analysis": "qwen3:8b"}


def test_openai_compatible_payload_uses_role_model(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode())
        return FakeResponse({"choices": [{"message": {"content": "done"}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = OpenAICompatibleClient(
        roles=RoleRegistry({"analysis": "model-a"}),
        base_url="https://gateway.example/v1",
    )

    response = client.complete([], role="analysis")

    assert response.content == "done"
    assert captured["url"] == "https://gateway.example/v1/chat/completions"
    assert captured["payload"]["model"] == "model-a"


def test_openai_structured_validates_required_schema(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return FakeResponse({"choices": [{"message": {"content": '{"answer": "yes"}'}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = OpenAICompatibleClient(
        roles=RoleRegistry({"analysis": "model-a"}),
        base_url="https://gateway.example/v1",
    )

    result = client.structured(
        [],
        role="analysis",
        schema={
            "type": "object",
            "required": ["answer"],
            "properties": {"answer": {"type": "string"}},
        },
    )

    assert result == {"answer": "yes"}


def test_openai_structured_rejects_missing_required_key(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return FakeResponse({"choices": [{"message": {"content": "{}"}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = OpenAICompatibleClient(
        roles=RoleRegistry({"analysis": "model-a"}),
        base_url="https://gateway.example/v1",
    )

    with pytest.raises(StructuredOutputError):
        client.structured([], role="analysis", schema={"type": "object", "required": ["answer"]})


def test_ollama_structured_rejects_wrong_type(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return FakeResponse({"message": {"content": '{"score": "high"}'}})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = OllamaClient(roles=RoleRegistry({"analysis": "model-a"}))

    with pytest.raises(StructuredOutputError):
        client.structured(
            [],
            role="analysis",
            schema={"type": "object", "properties": {"score": {"type": "number"}}},
        )


def test_openai_client_retries_bounded_failures(monkeypatch) -> None:
    attempts = {"count": 0}

    def fake_urlopen(request, timeout):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise urllib.error.URLError("temporary")
        return FakeResponse({"choices": [{"message": {"content": "done"}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = OpenAICompatibleClient(
        roles=RoleRegistry({"analysis": "model-a"}),
        base_url="https://gateway.example/v1",
        retry_attempts=1,
        retry_backoff_seconds=0.0,
    )

    response = client.complete([], role="analysis")

    assert response.content == "done"
    assert attempts["count"] == 2
