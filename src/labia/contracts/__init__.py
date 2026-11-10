"""Contrato de dados: a fonte da verdade do formato dos arquivos que o motor escreve e o painel lê.

Modelos Pydantic -> JSON Schema (schemas/) -> tipos TypeScript do painel.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from labia.contracts.audit import AuditFile
from labia.contracts.metrics import MetricsFile
from labia.contracts.replay import ReplayFile
from labia.contracts.summary import SummaryFile
from labia.contracts.versions import VersionsFile

#: Arquivo publicado -> modelo que o descreve.
CONTRACT_FILES: dict[str, type[BaseModel]] = {
    "results/summary.json": SummaryFile,
    "results/metrics.json": MetricsFile,
    "results/replay.json": ReplayFile,
    "results/audit_findings.json": AuditFile,
    "site-data/versions.json": VersionsFile,
}


def schema_name(published_path: str) -> str:
    return Path(published_path).stem + ".schema.json"


def export_schemas(out_dir: Path) -> list[Path]:
    """Escreve um JSON Schema por arquivo do contrato. Saída determinística, para a CI comparar."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for published, model in CONTRACT_FILES.items():
        target = out_dir / schema_name(published)
        schema = model.model_json_schema(mode="serialization")
        schema["$id"] = f"https://github.com/deniscarvalho-tech/labia/schemas/{target.name}"
        target.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(target)
    return written


def validate_file(published_path: str, path: Path) -> BaseModel:
    """Lê e valida um arquivo publicado contra o seu modelo; levanta ValidationError se divergir."""
    model = CONTRACT_FILES[published_path]
    return model.model_validate_json(path.read_text(encoding="utf-8"))


__all__ = [
    "CONTRACT_FILES",
    "AuditFile",
    "MetricsFile",
    "ReplayFile",
    "SummaryFile",
    "VersionsFile",
    "export_schemas",
    "schema_name",
    "validate_file",
]
