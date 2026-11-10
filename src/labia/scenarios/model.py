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
