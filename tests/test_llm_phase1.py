import json

from evolooption.cli.setup import main
from evolooption.llm.config import LLMConfig
from evolooption.llm.openai_compatible import OpenAICompatibleClient
from evolooption.llm.roles import RoleRegistry


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

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "done"}}]}).encode()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode())
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = OpenAICompatibleClient(
        roles=RoleRegistry({"analysis": "model-a"}),
        base_url="https://gateway.example/v1",
    )

    response = client.complete([], role="analysis")

    assert response.content == "done"
    assert captured["url"] == "https://gateway.example/v1/chat/completions"
    assert captured["payload"]["model"] == "model-a"
