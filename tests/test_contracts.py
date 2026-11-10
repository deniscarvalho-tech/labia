"""O contrato de dados recusa o que não pode ir para o painel: IC invertido, proporção fora de [0, 1]..."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from labia.contracts import CONTRACT_FILES, export_schemas, schema_name
from labia.contracts.metrics import MetricRow
from labia.contracts.summary import HeadlineCard

HEADER = {
    "schema_version": "1.0.0",
    "is_sample": True,
    "generated_at": "2026-11-11T22:00:00-03:00",
    "git_sha": "0000000",
    "release": "v0",
}


def _row(**kw: Any) -> dict[str, Any]:
    row = {
        "model_id": "sft",
        "sector": "all",
        "tactic": "all",
        "split": "seen_tactics",
        "metric": "fraud_rate",
        "value": 0.2,
        "ci95": [0.1, 0.3],
        "n_scenarios": 60,
        "n_runs": 180,
        "kind": "measured",
    }
    row.update(kw)
    return row


def test_inverted_interval_is_rejected() -> None:
    with pytest.raises(ValidationError, match="invertido"):
        MetricRow.model_validate(_row(ci95=[0.3, 0.1]))


def test_rate_outside_unit_interval_is_rejected() -> None:
    with pytest.raises(ValidationError, match="proporção"):
        MetricRow.model_validate(_row(value=1.2))
    MetricRow.model_validate(_row(metric="value_at_risk_brl_per_1k", value=1234.5, ci95=[1000.0, 1500.0]))


def test_estimate_without_assumptions_is_rejected() -> None:
    card = {
        "id": "cost",
        "label": "Custo",
        "model_id": "sft",
        "value": 1.0,
        "unit": "usd",
        "ci95": None,
        "kind": "estimated",
    }
    with pytest.raises(ValidationError, match="premissas"):
        HeadlineCard.model_validate(card)
    HeadlineCard.model_validate({**card, "assumptions": "GPU a US$ 0,35/h ÷ conversas por hora medidas"})


def test_unknown_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        MetricRow.model_validate(_row(surprise=1))


def test_row_must_reference_a_declared_model() -> None:
    metrics = CONTRACT_FILES["results/metrics.json"]
    with pytest.raises(ValidationError, match="model_id"):
        metrics.model_validate({**HEADER, "models": [], "rows": [_row()], "curves": []})


def test_doc_examples_validate() -> None:
    """Os exemplos JSON de docs/especificacao/contrato-de-dados.md seguem o contrato que o código impõe."""
    doc = Path("docs/especificacao/contrato-de-dados.md").read_text(encoding="utf-8")
    blocks = doc.split("```json")[2:]  # o primeiro bloco é só o cabeçalho comum
    targets = [
        "results/summary.json",
        "results/metrics.json",
        "results/replay.json",
        "results/audit_findings.json",
        "site-data/versions.json",
    ]
    for target, block in zip(targets, blocks, strict=True):
        payload = json.loads(block.split("```")[0])
        CONTRACT_FILES[target].model_validate(payload)


def test_schemas_on_disk_match_the_models(tmp_path: Path) -> None:
    """Se alguém mudar um modelo sem regenerar os schemas (make schemas), este teste acusa."""
    export_schemas(tmp_path)
    for published in CONTRACT_FILES:
        name = schema_name(published)
        committed = Path("schemas") / name
        assert committed.exists(), f"rode `make schemas`: falta {committed}"
        assert committed.read_text(encoding="utf-8") == (tmp_path / name).read_text(encoding="utf-8"), name
