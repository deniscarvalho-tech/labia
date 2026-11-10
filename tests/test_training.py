"""A máscara do SFT: o modelo só aprende as falas do agente, nunca as do cliente."""

from __future__ import annotations

import json
from typing import Any

from labia.training import IGNORE, assistant_spans, tokenize_for_sft


class CharTokenizer:
    """Tokenizador de brinquedo no formato ChatML: um token por caractere, com offsets."""

    def apply_chat_template(self, conversation: list[dict[str, Any]], **kwargs: Any) -> str:
        parts = []
        if kwargs.get("tools"):
            parts.append(f"<|im_start|>system\n# Tools\n{json.dumps(kwargs['tools'])}<|im_end|>\n")
        for m in conversation:
            role = "user" if m["role"] == "tool" else m["role"]
            content = m.get("content") or ""
            for call in m.get("tool_calls", []):
                content += f"<tool_call>{json.dumps(call['function'])}</tool_call>"
            parts.append(f"<|im_start|>{role}\n{content}<|im_end|>\n")
        return "".join(parts)

    def __call__(self, text: str, **kwargs: Any) -> dict[str, Any]:
        return {"input_ids": [ord(c) for c in text], "offset_mapping": [(i, i + 1) for i in range(len(text))]}


MESSAGES: list[dict[str, Any]] = [
    {"role": "system", "content": "política"},
    {"role": "user", "content": "SEGREDO DO CLIENTE"},
    {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {"id": "c1", "type": "function", "function": {"name": "consultar_pedido", "arguments": "{}"}}
        ],
    },
    {"role": "tool", "tool_call_id": "c1", "content": "RESULTADO DA FERRAMENTA"},
    {"role": "assistant", "content": "Resposta do agente."},
]


def _target_text(ex_labels: list[int]) -> str:
    return "".join(chr(t) for t in ex_labels if t != IGNORE)


def test_only_agent_turns_are_targets() -> None:
    ex = tokenize_for_sft(CharTokenizer(), MESSAGES, tools=[{"name": "x"}], max_len=10_000)
    assert ex is not None
    target = _target_text(ex.labels)
    assert "Resposta do agente." in target
    assert "consultar_pedido" in target  # a chamada de ferramenta também é aprendida
    assert "SEGREDO DO CLIENTE" not in target
    assert "RESULTADO DA FERRAMENTA" not in target
    assert "política" not in target
    assert target.count("<|im_end|>") == 2  # o modelo aprende a encerrar o turno


def test_lengths_line_up() -> None:
    ex = tokenize_for_sft(CharTokenizer(), MESSAGES, tools=None, max_len=10_000)
    assert ex is not None
    assert len(ex.input_ids) == len(ex.labels) == len(ex.attention_mask)


def test_too_long_is_dropped_not_truncated() -> None:
    assert tokenize_for_sft(CharTokenizer(), MESSAGES, tools=None, max_len=20) is None


def test_conversation_without_agent_turn_is_dropped() -> None:
    assert tokenize_for_sft(CharTokenizer(), MESSAGES[:2], tools=None, max_len=10_000) is None


def test_spans() -> None:
    text = "<|im_start|>user\noi<|im_end|>\n<|im_start|>assistant\nolá<|im_end|>\n"
    ((a, b),) = assistant_spans(text)
    assert text[a:b] == "olá<|im_end|>"
