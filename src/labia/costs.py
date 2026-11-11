"""Custo estimado por mil conversas e o ponto de equilíbrio entre servir o próprio modelo e pagar uma API.

Tudo aqui é ESTIMADO: a vazão e os tokens são medidos nas avaliações, mas os preços são públicos, de
terceiros, e o projeto não pagou nada. Cada preço vem de configs/precos.json com a fonte e a data.

- Modelo próprio: uma GPU dedicada custa o mesmo por hora, ocupada ou não. O custo mensal é fixo até a
  capacidade da GPU. A vazão vem da avaliação, em que o agente teve uma T4 só para ele, mas esperava o
  cliente simulado a cada turno; por isso a capacidade medida é um limite inferior (e o custo por
  conversa, um limite superior).
- API: custo linear no volume, pelos tokens medidos de cada conversa e pelo preço por milhão de tokens.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from labia.conversation import ConversationRecord

HOURS_PER_MONTH = 730


@dataclass(frozen=True)
class Price:
    valor: float
    unidade: str
    fonte: str
    consultado_em: str
    nota: str = ""


def tokens_per_conversation(records: list[ConversationRecord]) -> tuple[float, float]:
    """Média de tokens de entrada e de saída do agente por conversa (todas as chamadas, sem cache)."""
    if not records:
        return 0.0, 0.0
    prompt = sum(s.prompt_tokens for r in records for s in r.agent_stats if not s.cached)
    completion = sum(s.completion_tokens for r in records for s in r.agent_stats if not s.cached)
    return prompt / len(records), completion / len(records)


def self_hosted(n_conversations: int, hours: float, gpu: Price) -> dict[str, Any]:
    per_hour = n_conversations / hours
    return {
        "conversas_por_hora_de_gpu": round(per_hour, 1),
        "usd_por_mil_conversas": round(1000 / per_hour * gpu.valor, 4),
        "usd_por_mes_gpu_dedicada": round(gpu.valor * HOURS_PER_MONTH, 2),
        "capacidade_por_mes": int(per_hour * HOURS_PER_MONTH),
    }


def api_cost(
    prompt_tokens: float, completion_tokens: float, price_in: Price, price_out: Price
) -> dict[str, Any]:
    per_conversation = prompt_tokens / 1e6 * price_in.valor + completion_tokens / 1e6 * price_out.valor
    return {
        "tokens_entrada_por_conversa": round(prompt_tokens),
        "tokens_saida_por_conversa": round(completion_tokens),
        "usd_por_conversa": per_conversation,
        "usd_por_mil_conversas": round(per_conversation * 1000, 4),
    }


def break_even(monthly_fixed_usd: float, api_usd_per_conversation: float) -> int | None:
    """Conversas por mês a partir das quais a GPU dedicada sai mais barata que a API."""
    if api_usd_per_conversation <= 0:
        return None
    return int(monthly_fixed_usd / api_usd_per_conversation) + 1


def as_json(price: Price) -> dict[str, Any]:
    return asdict(price)
