"""results/audit_findings.json: o relatório de auditoria em formato de dados."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from labia.contracts.common import CI95, Header, Kind, Sector, Strict, Tactic, TrustLink

Severity = Literal["low", "medium", "high", "critical"]


class AuditScope(Strict):
    agents: list[str]
    sectors: list[Sector]
    tactics: list[Tactic]
    n_conversations: int = Field(ge=0)


class Frequency(Strict):
    value: float = Field(ge=0.0, le=1.0)
    ci95: CI95
    kind: Kind


class Retest(Strict):
    status: Literal["not_retested", "fixed", "still_failing"]
    version: str | None


class Finding(Strict):
    id: str = Field(pattern=r"^ACH-\d{3}$")
    title: str
    severity: Severity
    rule_ids: list[str]
    trust_link: TrustLink
    models_affected: list[str]
    frequency: Frequency
    value_at_risk_brl_per_1k: float = Field(ge=0.0)
    evidence: list[str]
    root_cause: str
    recommendation: str
    retest: Retest


class AuditFile(Header):
    scope: AuditScope
    findings: list[Finding]
