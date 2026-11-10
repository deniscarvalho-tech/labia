"""Tipos compartilhados por todos os arquivos do contrato de dados (docs/especificacao/contrato-de-dados.md)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

SCHEMA_VERSION: Literal["1.0.0"] = "1.0.0"


class Strict(BaseModel):
    """Base de todos os modelos do contrato: campos desconhecidos são erro, não silêncio."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=True)


class Sector(StrEnum):
    BANK = "bank"
    DELIVERY = "delivery"
    RETAIL = "retail"
    ALL = "all"


class Tactic(StrEnum):
    NONE = "none"
    AUTHORITY = "authority"
    INSTITUTIONAL_THREAT = "institutional_threat"
    URGENCY_EMOTION = "urgency_emotion"
    FAKE_PRIOR_PROMISE = "fake_prior_promise"
    SPLIT_REQUEST = "split_request"
    FAKE_PROOF = "fake_proof"
    ALL = "all"


class Split(StrEnum):
    SEEN_TACTICS = "seen_tactics"
    HELDOUT_TACTIC = "heldout_tactic"
    HELDOUT_SECTOR = "heldout_sector"
    ALL_TEST = "all_test"


class Defense(StrEnum):
    STANDARD = "standard"
    REINFORCED = "reinforced"


class Verdict(StrEnum):
    FRAUD_BLOCKED = "fraud_blocked"
    FRAUD_PASSED = "fraud_passed"
    SERVED_CORRECTLY = "served_correctly"
    FRICTION_DENIED = "friction_denied"
    FRICTION_ESCALATED = "friction_escalated"
    OVERGRANT = "overgrant"


class TrustLink(StrEnum):
    ACTOR_AUTHORITY = "actor_authority"
    ASSET_CONTROL = "asset_control"
    VERIFICATION_SUFFICIENCY = "verification_sufficiency"
    TRANSACTION_PATH = "transaction_path"


class RootCause(StrEnum):
    CLAIM_ACCEPTED_WITHOUT_CHECK = "claim_accepted_without_check"
    CHECKED_BUT_IGNORED = "checked_but_ignored"
    EXCEPTION_MISAPPLIED = "exception_misapplied"
    LOST_CUMULATIVE_COUNT = "lost_cumulative_count"
    PRESSURE_WITHOUT_NEW_FACT = "pressure_without_new_fact"
    THIRD_PARTY_ASSET = "third_party_asset"
    OTHER = "other"


class MetricName(StrEnum):
    FRAUD_RATE = "fraud_rate"
    FRICTION_RATE = "friction_rate"
    FRICTION_DENIED_RATE = "friction_denied_rate"
    FRICTION_ESCALATED_RATE = "friction_escalated_rate"
    OVERGRANT_RATE = "overgrant_rate"
    PASS3 = "pass3"
    VALID_TOOL_CALL_RATE = "valid_tool_call_rate"
    VERIFIED_BEFORE_ACTING_RATE = "verified_before_acting_rate"
    VALUE_AT_RISK_BRL_PER_1K = "value_at_risk_brl_per_1k"
    COST_PER_1K_USD = "cost_per_1k_usd"
    LATENCY_TURN_P50_S = "latency_turn_p50_s"
    LATENCY_TURN_P95_S = "latency_turn_p95_s"
    LATENCY_DECISION_P50_S = "latency_decision_p50_s"


#: Métricas que são proporções e por isso precisam ficar entre 0 e 1.
RATE_METRICS: frozenset[str] = frozenset(
    {
        MetricName.FRAUD_RATE,
        MetricName.FRICTION_RATE,
        MetricName.FRICTION_DENIED_RATE,
        MetricName.FRICTION_ESCALATED_RATE,
        MetricName.OVERGRANT_RATE,
        MetricName.PASS3,
        MetricName.VALID_TOOL_CALL_RATE,
        MetricName.VERIFIED_BEFORE_ACTING_RATE,
    }
)


class Kind(StrEnum):
    MEASURED = "measured"
    ESTIMATED = "estimated"


def _ordered_interval(value: tuple[float, float] | None) -> tuple[float, float] | None:
    if value is not None and value[0] > value[1]:
        raise ValueError(f"ci95 invertido: o limite inferior {value[0]} é maior que o superior {value[1]}")
    return value


#: Intervalo de confiança de 95%: [inferior, superior], ou null quando não se aplica.
CI95 = Annotated[tuple[float, float] | None, AfterValidator(_ordered_interval)]

GitSha = Annotated[str, Field(pattern=r"^[0-9a-f]{7,40}$")]


class Header(Strict):
    """Cabeçalho comum a todo arquivo de resultado."""

    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    is_sample: bool = Field(description="true quando os dados são de exemplo; o script de publicação recusa.")
    generated_at: datetime
    git_sha: GitSha
    release: str = Field(pattern=r"^v\d+(\.\d+)*$")
