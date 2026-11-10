"""Cliente de LLM no formato da API da OpenAI, com cache em disco e teto de chamadas.

Todo modelo do projeto é chamado por aqui: llama.cpp e vLLM no Kaggle, Google AI Studio e NVIDIA na
avaliação. O mesmo código avalia qualquer modelo (decisão 9 do plano).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class RawToolCall:
    id: str
    name: str
    arguments: str  # o JSON como o modelo escreveu, ainda sem parsear


@dataclass
class ChatResponse:
    content: str
    tool_calls: list[RawToolCall] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0
    finish_reason: str | None = None
    cached: bool = False


@dataclass(frozen=True)
class ChatRequest:
    model: str
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] | None = None
    temperature: float = 0.7
    top_p: float = 0.95
    max_tokens: int = 1024
    seed: int | None = None

    def cache_key(self) -> str:
        payload = json.dumps(asdict(self), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ChatClient(Protocol):
    def complete(self, request: ChatRequest) -> ChatResponse: ...


class BudgetExceeded(RuntimeError):
    """O teto de chamadas da rodada foi atingido: a rodada para em vez de gastar além do combinado."""


_TOOL_CALL_IN_TEXT = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)


def extract_text_tool_calls(content: str) -> tuple[str, list[RawToolCall]]:
    """Plano B: alguns servidores devolvem a chamada dentro do texto (<tool_call>{...}</tool_call>)."""
    calls: list[RawToolCall] = []
    for i, match in enumerate(_TOOL_CALL_IN_TEXT.finditer(content)):
        try:
            data = json.loads(match.group(1))
            name = str(data.get("name", ""))
            args = data.get("arguments", {})
        except json.JSONDecodeError:
            name, args = "", match.group(1)
        calls.append(
            RawToolCall(
                id=f"text_call_{i}",
                name=name,
                arguments=args if isinstance(args, str) else json.dumps(args, ensure_ascii=False),
            )
        )
    return _TOOL_CALL_IN_TEXT.sub("", content).strip(), calls


class OpenAICompatClient:
    """Fala com qualquer servidor compatível com /v1/chat/completions."""

    def __init__(self, base_url: str, api_key: str = "sem-chave", timeout_s: float = 300.0) -> None:
        from openai import OpenAI

        self._client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout_s, max_retries=3)

    def complete(self, request: ChatRequest) -> ChatResponse:
        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_tokens": request.max_tokens,
        }
        if request.tools:
            kwargs["tools"] = request.tools
        if request.seed is not None:
            kwargs["seed"] = request.seed
        start = time.perf_counter()
        resp = self._client.chat.completions.create(**kwargs)
        latency = time.perf_counter() - start
        choice = resp.choices[0]
        content = choice.message.content or ""
        calls = [
            RawToolCall(id=tc.id or f"call_{i}", name=tc.function.name, arguments=tc.function.arguments or "")
            for i, tc in enumerate(choice.message.tool_calls or [])
            if getattr(tc, "function", None) is not None
        ]
        if not calls and "<tool_call>" in content:
            content, calls = extract_text_tool_calls(content)
        usage = resp.usage
        return ChatResponse(
            content=content.strip(),
            tool_calls=calls,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            latency_s=latency,
            finish_reason=choice.finish_reason,
        )


class CachedClient:
    """Guarda cada resposta em disco pela chave do pedido. Repetir uma rodada não chama o modelo de novo.

    A semente da rodada entra na chave, então as 3 rodadas de um cenário são chamadas diferentes.
    """

    def __init__(self, inner: ChatClient, cache_dir: Path, max_calls: int | None = None) -> None:
        self.inner = inner
        self.cache_dir = cache_dir
        self.max_calls = max_calls
        self.calls_made = 0
        self.cache_hits = 0

    def _path(self, key: str) -> Path:
        return self.cache_dir / key[:2] / f"{key}.json"

    def complete(self, request: ChatRequest) -> ChatResponse:
        path = self._path(request.cache_key())
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            data["tool_calls"] = [RawToolCall(**tc) for tc in data["tool_calls"]]
            self.cache_hits += 1
            return ChatResponse(**{**data, "cached": True})
        if self.max_calls is not None and self.calls_made >= self.max_calls:
            raise BudgetExceeded(f"teto de {self.max_calls} chamadas atingido nesta rodada")
        response = self.inner.complete(request)
        self.calls_made += 1
        path.parent.mkdir(parents=True, exist_ok=True)
        record = asdict(response)
        record["cached"] = False
        path.write_bytes(json.dumps(record, ensure_ascii=False).encode("utf-8"))
        return response
