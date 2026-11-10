"""Peças comuns aos construtores de situação dos dois setores."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from labia.contracts.common import Tactic
from labia.scenarios.model import Action, Entitlement


@dataclass
class Ctx:
    """O contexto de geração de um cenário: semente, divisão, tática e o "agora" da sandbox."""

    rng: random.Random
    split: str
    tactic: Tactic
    agora: datetime

    def ident(self, prefix: str, width: int = 5) -> str:
        """Identificadores com faixas separadas por divisão: treino e teste nunca compartilham um ID."""
        low = 10 ** (width - 1)
        mid = 5 * low
        lo, hi = (low, mid - 1) if self.split == "train" else (mid, 10 * low - 1)
        return f"{prefix}-{self.rng.randint(lo, hi)}"

    def ago(self, lo_min: int, hi_min: int) -> datetime:
        return self.agora - timedelta(minutes=self.rng.randint(lo_min, hi_min))

    def days_ago(self, lo: int, hi: int) -> datetime:
        return self.agora - timedelta(days=self.rng.randint(lo, hi))

    def chance(self, p: float) -> bool:
        return self.rng.random() < p

    def pick(self, options: list[str]) -> str:
        return self.rng.choice(options)


@dataclass
class PromiseSpec:
    """Para a tática de promessa (T4): como descrever, no protocolo, a promessa que o cliente cita."""

    description: str


@dataclass
class Built:
    """A saída de um construtor de situação: o estado do sistema e o que o cliente sabe e quer."""

    variant: str
    state: dict[str, object]
    goal_actions: list[Action]
    entitlements: list[Entitlement]
    escalation_mandated: bool
    situation: str
    goal: str
    truth: str
    facts: dict[str, str]
    promise: PromiseSpec | None = None
    steps: tuple[str, ...] = ()
    authority_claim: str | None = None
    note: str = ""
    extra: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SituationDef:
    """Uma situação da sandbox: um pedido típico de cliente que tem um lado golpe e um lado legítimo."""

    name: str
    sector: str
    rule: str
    #: build(ctx, session_cpf, session_name, legit) -> Built
    build: Callable[..., Built]
    #: A promessa registrada (G5) pode autorizar a ação? Falso para G2 e para o destino do dinheiro.
    promise_applies: bool = True
    #: Situação exclusiva da tática de fracionamento (T5), que fica fora do treino.
    split_only: bool = False


def money(value: float) -> str:
    """R$ 1.234,56, como um brasileiro escreve."""
    whole, cents = f"{value:,.2f}".split(".")
    return f"R$ {whole.replace(',', '.')},{cents}"


def hhmm(moment: datetime) -> str:
    return moment.strftime("%Hh%M")
