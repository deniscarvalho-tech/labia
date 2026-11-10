"""Construtores de estado para testes: montam os fatos de um cenário à mão, sem o gerador."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from labia.contracts.common import Tactic
from labia.sandbox.core import Session
from labia.scenarios.model import Action, CustomerBrief, Entitlement, Scenario
from labia.verifier import CallEvent, Report, verify

SESSION = Session(cpf="412.875.093-00", nome="Rita Boaventura")
OTHER_CPF = "538.114.270-11"
NOW = datetime(2026, 11, 10, 21, 30)

_BRIEF = CustomerBrief(
    persona="teste", situation="teste", goal="teste", truth="teste", tactic_instructions="teste"
)


def order(**kw: Any) -> dict[str, Any]:
    """Pedido do par 2 da especificação (QTI-58213, R$ 72,89), com qualquer campo sobrescrito."""
    base: dict[str, Any] = {
        "id": "QTI-58213",
        "cpf": SESSION.cpf,
        "restaurante": "Cantina da Praça",
        "itens": [
            {"nome": "Combo smash burger", "valor": 42.90},
            {"nome": "Batata média", "valor": 14.00},
            {"nome": "Refrigerante lata", "valor": 8.00},
        ],
        "taxa_entrega": 7.99,
        "pagamento": {"forma": "cartao_credito", "final": "4411"},
        "status": "entregue",
        "endereco": "Rua das Acácias, 120",
        "horario_prometido": (NOW - timedelta(minutes=55)).isoformat(),
        "horario_entrega": (NOW - timedelta(minutes=49)).isoformat(),
        "confirmacao": "codigo",
        "embalagem_conferida": False,
    }
    base.update(kw)
    return base


def delivery_state(*orders: dict[str, Any], **customer: Any) -> dict[str, Any]:
    me: dict[str, Any] = {"cpf": SESSION.cpf, "nome": SESSION.nome, "enderecos": ["Rua das Acácias, 120"]}
    me.update(customer)
    return {"agora": NOW.isoformat(), "clientes": [me], "pedidos": list(orders), "protocolos": []}


def account(**kw: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "cpf": SESSION.cpf,
        "titular": SESSION.nome,
        "segmento": "padrao",
        "saldo": 6200.00,
        "limite_atual": 3000.00,
        "limite_max_preaprovado": 8000.00,
    }
    base.update(kw)
    return base


def bank_state(*accounts: dict[str, Any], **kw: Any) -> dict[str, Any]:
    return {"agora": NOW.isoformat(), "contas": list(accounts) or [account()], **kw}


def scenario(
    sector: str,
    state: dict[str, Any],
    *,
    legit: bool,
    entitlements: list[Entitlement] | None = None,
    tactic: Tactic = Tactic.NONE,
    mandated: bool = False,
    goal: list[Action] | None = None,
) -> Scenario:
    return Scenario(
        id="teste",
        sector=sector,
        situation="teste",
        rule="teste",
        legit=legit,
        tactic=tactic,
        seed=0,
        split="test",
        variant="teste",
        session=SESSION,
        state=state,
        customer=_BRIEF,
        goal_actions=tuple(goal or ()),
        entitlements=tuple(entitlements or ()),
        escalation_mandated=mandated,
    )


def run(s: Scenario, *calls: tuple[str, dict[str, Any]], asked_human: bool = False) -> Report:
    """Roda o verificador sobre uma sequência de chamadas, uma por turno."""
    events = [CallEvent(turn=i + 1, name=name, arguments=args) for i, (name, args) in enumerate(calls)]
    return verify(s, events, customer_asked_human=asked_human)


def look(order_id: str = "QTI-58213") -> tuple[str, dict[str, Any]]:
    return ("consultar_pedido", {"id_pedido": order_id})


def look_customer() -> tuple[str, dict[str, Any]]:
    return ("consultar_cliente", {"cpf": SESSION.cpf})
