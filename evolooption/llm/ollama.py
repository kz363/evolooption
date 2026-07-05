from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from evolooption.llm.client import (
    LLMClient,
    LLMMessage,
    LLMResponse,
    validate_structured_output,
)
from evolooption.llm.roles import RoleRegistry


@dataclass
class OllamaClient(LLMClient):
    roles: RoleRegistry
    host: str = "http://localhost:11434"
    timeout_seconds: float = 120.0
    retry_attempts: int = 2
    retry_backoff_seconds: float = 0.25

    def complete(self, messages: list[LLMMessage], *, role: str) -> LLMResponse:
        model = self.roles.model_for(role)
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        raw = self._post_json("/api/chat", payload)
        content = str(raw.get("message", {}).get("content", ""))
        return LLMResponse(content=content, raw=raw)

    def structured(
        self,
        messages: list[LLMMessage],
        *,
        role: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        prompt_messages = [
            *messages,
            LLMMessage(role="system", content=_schema_instruction(schema)),
        ]
        response = self.complete(prompt_messages, role=role)
        return validate_structured_output(json.loads(response.content), schema)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.host.rstrip('/')}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(self.retry_attempts + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.URLError:
                if attempt >= self.retry_attempts:
                    raise
                time.sleep(self.retry_backoff_seconds * (2**attempt))
        raise RuntimeError("unreachable retry state")


def _schema_instruction(schema: dict[str, Any]) -> str:
    return "Return only JSON matching this schema: " + json.dumps(schema, sort_keys=True)
