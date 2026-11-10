"""O laço de conversa: cliente simulado e agente conversam dentro da sandbox, e o verificador julga."""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from labia.agents import Agent, Customer
from labia.contracts.common import Defense, Tactic, TrustLink, Verdict
from labia.llm import BudgetExceeded
from labia.prompts import REMINDER, agent_system_prompt
from labia.sandbox import get_sector
from labia.sandbox.core import InvalidToolCall, Sector, Session, ToolCall
from labia.scenarios.model import Scenario
from labia.verifier import CallEvent, verify

END_TOKEN = "[FIM]"
ESCALATION_RESULT = {
    "ok": True,
    "mensagem": "Atendimento transferido para um atendente humano. O chat foi encerrado.",
}

#: O cliente pediu um humano? (G3: transferir nesse caso nunca é atrito.)
HUMAN_REQUEST = re.compile(
    r"\b(humano|pessoa de verdade|atendente (humano|real|de verdade)|falar com (algu[eé]m|uma pessoa|um atendente|o gerente))\b",
    re.IGNORECASE,
)


class Message(BaseModel):
    turn: int
    role: Literal["customer", "agent", "tool"]
    content: Any
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    name: str | None = None


class AgentCallStat(BaseModel):
    turn: int
    latency_s: float
    prompt_tokens: int
    completion_tokens: int
    cached: bool


class ConversationRecord(BaseModel):
    """Tudo o que aconteceu numa conversa, mais o veredito do verificador. Uma linha do JSONL de uma rodada."""

    scenario_id: str
    model_id: str
    defense: Defense
    run: int
    sector: str
    situation: str
    tactic: Tactic
    legit: bool
    split: str
    messages: list[Message]
    agent_history: list[dict[str, Any]]
    calls: list[dict[str, Any]]
    ended_by: Literal["customer", "escalated", "max_turns", "budget", "agent_stuck"]
    n_turns: int
    agent_stats: list[AgentCallStat]
    customer_asked_human: bool
    verdict: Verdict
    violated_rules: list[str]
    trust_link: TrustLink | None
    concession_turn: int | None
    value_at_risk: float
    escalated: bool
    escalation_mandated: bool
    process_ok: bool
    n_calls: int
    n_valid_calls: int
    n_benefit_actions: int
    n_benefit_actions_verified: int
    checked_protocols: bool
    blocked_without_check: bool
    reasons: list[str]

    @property
    def correct(self) -> bool:
        return self.verdict in (Verdict.SERVED_CORRECTLY, Verdict.FRAUD_BLOCKED)

    def turn_latencies(self) -> list[float]:
        """Tempo do agente por turno (soma das chamadas do turno), sem contar respostas vindas do cache."""
        per_turn: dict[int, float] = {}
        for s in self.agent_stats:
            if not s.cached:
                per_turn[s.turn] = per_turn.get(s.turn, 0.0) + s.latency_s
        return list(per_turn.values())


def execute(
    sector: Sector[Any], state: Any, session: Session, name: str, args: dict[str, Any] | None
) -> tuple[Any, bool]:
    """Executa uma chamada na sandbox e diz se ela era válida.

    Uma chamada inválida volta para o agente como erro, e ele pode tentar de novo.
    """
    if args is None:
        return {"erro": "os argumentos não são um JSON válido"}, False
    try:
        call = sector.validate(ToolCall(name, args))
    except InvalidToolCall as exc:
        return {"erro": f"chamada inválida: {exc}"}, False
    kind = sector.tools[call.name].kind
    if kind == "read":
        return sector.read(state, session, call), True
    if kind == "write":
        return sector.apply(state, session, call), True
    return ESCALATION_RESULT, True


def _parse(arguments: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(arguments) if arguments.strip() else {}
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def run_conversation(
    scenario: Scenario,
    agent: Agent,
    customer: Customer,
    *,
    model_id: str,
    defense: Defense = Defense.STANDARD,
    run: int = 1,
    max_turns: int = 8,
    max_steps: int = 6,
) -> ConversationRecord:
    sector = get_sector(scenario.sector)
    state = sector.initial_state(scenario.state)
    tools = sector.tool_schemas()
    history: list[dict[str, Any]] = [{"role": "system", "content": agent_system_prompt(scenario, defense)}]
    messages: list[Message] = []
    events: list[CallEvent] = []
    stats: list[AgentCallStat] = []
    dialogue: list[tuple[str, str]] = []
    ended_by: Literal["customer", "escalated", "max_turns", "budget", "agent_stuck"] = "max_turns"
    turn = 0

    try:
        for turn in range(1, max_turns + 1):
            text = customer.next_message(dialogue)
            finished = END_TOKEN in text
            text = text.replace(END_TOKEN, "").strip()
            if text:
                messages.append(Message(turn=turn, role="customer", content=text))
                dialogue.append(("customer", text))
            if finished or not text:
                ended_by = "customer"
                break
            content = text + (REMINDER if defense == Defense.REINFORCED else "")
            history.append({"role": "user", "content": content})

            escalated, answered = False, False
            for _ in range(max_steps):
                reply = agent.respond(history, tools)
                stats.append(
                    AgentCallStat(
                        turn=turn,
                        latency_s=reply.latency_s,
                        prompt_tokens=reply.prompt_tokens,
                        completion_tokens=reply.completion_tokens,
                        cached=reply.cached,
                    )
                )
                if not reply.tool_calls:
                    final = reply.content or "(sem resposta)"
                    history.append({"role": "assistant", "content": final})
                    messages.append(Message(turn=turn, role="agent", content=final))
                    dialogue.append(("agent", final))
                    answered = True
                    break
                history.append(
                    {
                        "role": "assistant",
                        "content": reply.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.name, "arguments": tc.arguments},
                            }
                            for tc in reply.tool_calls
                        ],
                    }
                )
                recorded = []
                for tc in reply.tool_calls:
                    args = _parse(tc.arguments)
                    events.append(CallEvent(turn=turn, name=tc.name, arguments=args))
                    result, valid = execute(sector, state, scenario.session, tc.name, args)
                    recorded.append(
                        {
                            "name": tc.name,
                            "arguments": args if args is not None else tc.arguments,
                            "valid": valid,
                        }
                    )
                    history.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )
                    if result is ESCALATION_RESULT:
                        escalated = True
                        break
                messages.append(
                    Message(turn=turn, role="agent", content=reply.content or "", tool_calls=recorded)
                )
                for rec, msg in zip(recorded, history[-len(recorded) :], strict=False):
                    messages.append(
                        Message(turn=turn, role="tool", name=rec["name"], content=json.loads(msg["content"]))
                    )
                if escalated:
                    break
            if escalated:
                ended_by = "escalated"
                break
            if not answered:
                ended_by = "agent_stuck"
                break
    except BudgetExceeded:
        ended_by = "budget"

    asked_human = any(HUMAN_REQUEST.search(t) for r, t in dialogue if r == "customer")
    report = verify(scenario, events, customer_asked_human=asked_human)
    return ConversationRecord(
        scenario_id=scenario.id,
        model_id=model_id,
        defense=defense,
        run=run,
        sector=scenario.sector,
        situation=scenario.situation,
        tactic=scenario.tactic,
        legit=scenario.legit,
        split=scenario.split,
        messages=messages,
        agent_history=history,
        calls=[{"turn": e.turn, "name": e.name, "arguments": e.arguments} for e in events],
        ended_by=ended_by,
        n_turns=turn,
        agent_stats=stats,
        customer_asked_human=asked_human,
        verdict=report.verdict,
        violated_rules=report.violated_rules,
        trust_link=report.trust_link,
        concession_turn=report.concession_turn,
        value_at_risk=report.value_at_risk,
        escalated=report.escalated,
        escalation_mandated=report.escalation_mandated,
        process_ok=report.process_ok,
        n_calls=report.n_calls,
        n_valid_calls=report.n_valid_calls,
        n_benefit_actions=report.n_benefit_actions,
        n_benefit_actions_verified=report.n_benefit_actions_verified,
        checked_protocols=report.checked_protocols,
        blocked_without_check=report.blocked_without_check,
        reasons=report.reasons,
    )
