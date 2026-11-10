"""results/summary.json: os números de destaque, já prontos para exibir."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import Field, model_validator

from labia.contracts.common import CI95, Header, Kind, Strict


class Comparison(Strict):
    model_id: str
    label: str
    value: float
    ci95: CI95


class HeadlineCard(Strict):
    """Um cartão que se descreve sozinho: o portfólio e o painel só renderizam."""

    id: str = Field(pattern=r"^[a-z0-9_]+$")
    label: str
    model_id: str
    value: float
    unit: Literal["ratio", "usd", "brl", "seconds", "count"]
    ci95: CI95
    kind: Kind
    assumptions: str | None = None
    comparison: Comparison | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _estimates_carry_assumptions(self) -> Self:
        if self.kind == Kind.ESTIMATED and not self.assumptions:
            raise ValueError(
                f"o cartão '{self.id}' é estimado e precisa trazer as premissas em 'assumptions'"
            )
        if self.unit == "ratio" and not 0.0 <= self.value <= 1.0:
            raise ValueError(f"o cartão '{self.id}' é uma proporção e precisa ficar entre 0 e 1")
        return self


class SummaryFile(Header):
    headline: list[HeadlineCard]
