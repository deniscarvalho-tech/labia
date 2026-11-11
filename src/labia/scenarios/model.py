"""O que é um cenário: os fatos, o cliente, a tática e o gabarito de uma conversa."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from labia.contracts.common import Tactic
from labia.sandbox.core import Session


class Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Action(Frozen):
    """Uma chamada de ferramenta escrita como dado (no cenário, é o que o cliente quer que o agente faça)."""

    tool: str
    arguments: dict[str, Any]


class Entitlement(Frozen):
    """Um direito do cliente: o que o agente precisava conceder para o atendimento estar correto.

    Fica satisfeito quando as ações *permitidas* da ferramenta `tool` sobre o alvo `target` somam pelo
    menos `min_value` (ou, com `min_value` 0, quando existe pelo menos uma). `kinds` restringe o motivo ou
    o tipo aceito (por exemplo, só `item_faltante`).
    """

    tool: str
    target: str
    min_value: float = 0.0
    kinds: tuple[str, ...] | None = None
    description: str


class CustomerBrief(Frozen):
    """Tudo o que o cliente simulado recebe. Ele nunca vê o estado do sistema, só o que um cliente saberia."""

    persona: str
    situation: str
    goal: str
    truth: str
    tactic_instructions: str
    facts: dict[str, str] = Field(default_factory=dict)
    #: Na tática de fracionamento, os pedidos em sequência.
    steps: tuple[str, ...] = ()


Split = Literal["train", "test"]


class Scenario(Frozen):
    id: str
    sector: Literal["bank", "delivery"]
    situation: str
    rule: str
    legit: bool
    tactic: Tactic
    seed: int
    split: Split
    variant: str
    session: Session
    state: dict[str, Any]
    customer: CustomerBrief
    goal_actions: tuple[Action, ...]
    entitlements: tuple[Entitlement, ...]
    escalation_mandated: bool
    note: str = ""


#: Combinações (situação, variante de base) em que a promessa legítima da tática T4 tem gabarito contestável:
#: a ação prometida já foi feita, mira algo que não existe, ou esbarra numa regra que o atendimento não
#: pode dispensar no mundo real (ordem judicial, prazo regulatório do MED). Achado na análise da geração
#: (docs/decisoes/0008-gabarito-contestavel.md). O teste congelado fica como está; a análise de
#: sensibilidade exclui estes cenários, e o gerador da v1 deixa de produzi-los.
CONTESTED_PROMISE_VARIANTS: frozenset[tuple[str, str]] = frozenset(
    {
        ("B1-estorno-tarifa", "ja-estornada"),
        ("B3-med-pix", "ja-contestado"),
        ("B3-med-pix", "fora-do-prazo"),
        ("B4-desbloqueio", "bloqueio-judicial"),
        ("D3-item-faltante", "item-inexistente"),
        ("D5-cupom-atraso", "cupom-ja-emitido"),
    }
)
PROMISE_SUFFIX = "+promessa-registrada"


def is_contested(scenario: Scenario) -> bool:
    """O cenário é um cliente honesto com promessa registrada cujo gabarito é contestável."""
    if not (scenario.legit and scenario.variant.endswith(PROMISE_SUFFIX)):
        return False
    return (scenario.situation, scenario.variant.removesuffix(PROMISE_SUFFIX)) in CONTESTED_PROMISE_VARIANTS
