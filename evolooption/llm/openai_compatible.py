from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Any

from evolooption.llm.client import LLMClient, LLMMessage, LLMResponse
from evolooption.llm.roles import RoleRegistry


@dataclass
class OpenAICompatibleClient(LLMClient):
    roles: RoleRegistry
    base_url: str
    api_key_env: str = "OPENAI_API_KEY"
    timeout_seconds: float = 120.0

    def complete(self, messages: list[LLMMessage], *, role: str) -> LLMResponse:
        payload = {
            "model": self.roles.model_for(role),
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        raw = self._post_json("/chat/completions", payload)
        content = str(raw.get("choices", [{}])[0].get("message", {}).get("content", ""))
        return LLMResponse(content=content, raw=raw)

    def structured(
        self,
        messages: list[LLMMessage],
        *,
        role: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "model": self.roles.model_for(role),
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": schema},
            },
        }
        raw = self._post_json("/chat/completions", payload)
        content = str(raw.get("choices", [{}])[0].get("message", {}).get("content", "{}"))
        return json.loads(content)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        api_key = os.environ.get(self.api_key_env, "")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
