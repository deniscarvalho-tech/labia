"""Sandbox: os sistemas fictícios que o agente opera, e as regras que dizem o que ele podia fazer."""

from __future__ import annotations

from typing import Any

from labia.sandbox.bank import BankSector
from labia.sandbox.core import InvalidToolCall, Sector, Session, ToolCall
from labia.sandbox.delivery import DeliverySector

SECTORS: dict[str, Sector[Any]] = {
    "bank": BankSector(),
    "delivery": DeliverySector(),
}


def get_sector(name: str) -> Sector[Any]:
    try:
        return SECTORS[name]
    except KeyError as exc:
        raise ValueError(f"setor desconhecido: {name}") from exc


__all__ = ["SECTORS", "InvalidToolCall", "Sector", "Session", "ToolCall", "get_sector"]
