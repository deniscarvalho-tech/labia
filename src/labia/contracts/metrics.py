"""results/metrics.json: todas as métricas em formato longo, uma linha por combinação."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import Field, model_validator

from labia.contracts.common import (
    CI95,
    RATE_METRICS,
    Defense,
    Header,
    Kind,
    MetricName,
    Sector,
    Split,
    Strict,
    Tactic,
)


class ModelInfo(Strict):
    id: str = Field(pattern=r"^[a-z0-9_+\-.]+$")
    label: str
    base_model: str | None
    params_b: float | None
    license: str
    access: Literal["self_hosted", "api"]
    defense: Defense


class MetricRow(Strict):
    model_id: str
    sector: Sector
    tactic: Tactic
    split: Split
    metric: MetricName
    value: float
    ci95: CI95
    n_scenarios: int = Field(ge=0)
    n_runs: int = Field(ge=0)
    kind: Kind

    @model_validator(mode="after")
    def _rates_between_zero_and_one(self) -> Self:
        if self.metric in RATE_METRICS:
            values = [self.value, *(self.ci95 or ())]
            if any(not 0.0 <= v <= 1.0 for v in values):
                raise ValueError(f"{self.metric} é uma proporção: valor e IC precisam ficar entre 0 e 1")
        return self


class CurvePoint(Strict):
    turn: int = Field(ge=0)
    value: float = Field(ge=0.0, le=1.0)
    ci95: CI95


class Curve(Strict):
    model_id: str
    type: Literal["resistance_by_turn"]
    split: Split
    points: list[CurvePoint]


class MetricsFile(Header):
    models: list[ModelInfo]
    rows: list[MetricRow]
    curves: list[Curve]

    @model_validator(mode="after")
    def _every_row_points_to_a_known_model(self) -> Self:
        known = {m.id for m in self.models}
        unknown = {r.model_id for r in self.rows} | {c.model_id for c in self.curves}
        missing = sorted(unknown - known)
        if missing:
            raise ValueError(f"model_id sem entrada em 'models': {missing}")
        return self
