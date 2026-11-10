"""results/replay.json: as conversas que o painel mostra no replay."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from labia.contracts.common import Defense, Header, RootCause, Sector, Strict, Tactic, TrustLink, Verdict


class ToolCallRecord(Strict):
    name: str
    arguments: dict[str, Any]
    valid: bool


class CustomerMessage(Strict):
    turn: int = Field(ge=1)
    role: Literal["customer"]
    content: str


class AgentMessage(Strict):
    turn: int = Field(ge=1)
    role: Literal["agent"]
    content: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class ToolMessage(Strict):
    turn: int = Field(ge=1)
    role: Literal["tool"]
    name: str
    content: Any


Message = Annotated[CustomerMessage | AgentMessage | ToolMessage, Field(discriminator="role")]


class RootCauseLabel(Strict):
    label: RootCause
    source: Literal["llm_judge", "human"]
    judge_model: str | None
    human_review: RootCause | None


class Highlight(Strict):
    turn: int = Field(ge=1)
    text: str


class ReplayConversation(Strict):
    id: str
    scenario_id: str
    model_id: str
    defense: Defense
    run: int = Field(ge=1)
    sector: Sector
    tactic: Tactic
    legit: bool
    verdict: Verdict
    violated_rules: list[str]
    trust_link: TrustLink | None
    concession_turn: int | None = Field(default=None, ge=1)
    root_cause: RootCauseLabel | None
    value_at_risk_brl: float = Field(ge=0.0)
    highlight: Highlight | None
    messages: list[Message]
    cost_usd: float | None = Field(default=None, ge=0.0)
    latency_s: float | None = Field(default=None, ge=0.0)


class ReplayFile(Header):
    conversations: list[ReplayConversation]
