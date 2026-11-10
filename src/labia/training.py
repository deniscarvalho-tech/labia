"""Preparação do dado de SFT: tokenizar a conversa e marcar só as falas do agente como alvo.

O modelo vê a conversa inteira (política, ferramentas, cliente, resultados das ferramentas), mas só é
treinado para produzir as falas e as chamadas do agente. Sem essa máscara, o aluno também aprenderia a
imitar o cliente golpista.

O tokenizador entra por "duck typing": qualquer objeto com `apply_chat_template` e chamada com
`return_offsets_mapping` serve. Assim a lógica é testada sem baixar modelo nenhum.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

IGNORE = -100  # rótulo que a função de perda ignora

#: Marcadores do formato ChatML, usado pelo Qwen.
ASSISTANT_START = "<|im_start|>assistant\n"
TURN_END = "<|im_end|>"


class Tokenizer(Protocol):
    def apply_chat_template(self, conversation: list[dict[str, Any]], **kwargs: Any) -> Any: ...

    def __call__(self, text: str, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class Example:
    input_ids: list[int]
    attention_mask: list[int]
    labels: list[int]

    @property
    def n_target(self) -> int:
        return sum(1 for label in self.labels if label != IGNORE)


def assistant_spans(text: str, start: str = ASSISTANT_START, end: str = TURN_END) -> list[tuple[int, int]]:
    """Trechos (início, fim) do texto que são fala do agente, incluindo o marcador de fim de turno."""
    pattern = re.escape(start) + r"(.*?" + re.escape(end) + r")"
    return [(m.start(1), m.end(1)) for m in re.finditer(pattern, text, re.DOTALL)]


def tokenize_for_sft(
    tokenizer: Tokenizer,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None,
    *,
    max_len: int,
    start: str = ASSISTANT_START,
    end: str = TURN_END,
) -> Example | None:
    """Tokeniza a conversa e rotula só os tokens das falas do agente.

    Devolve None quando a conversa passa de `max_len` tokens. Cortar no meio ensinaria uma conversa
    que não termina; é melhor descartar e contar quantas foram descartadas.
    """
    text = tokenizer.apply_chat_template(messages, tools=tools, tokenize=False)
    spans = assistant_spans(text, start, end)
    encoded = tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)
    ids: list[int] = list(encoded["input_ids"])
    if len(ids) > max_len:
        return None
    labels = []
    span_i = 0
    for token, (a, b) in zip(ids, encoded["offset_mapping"], strict=True):
        while span_i < len(spans) and spans[span_i][1] <= a:
            span_i += 1
        inside = span_i < len(spans) and spans[span_i][0] <= a and b <= spans[span_i][1] and b > a
        labels.append(token if inside else IGNORE)
    example = Example(input_ids=ids, attention_mask=[1] * len(ids), labels=labels)
    return example if example.n_target > 0 else None
