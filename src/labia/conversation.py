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
EndReason = Literal["customer", "escalated", "max_turns", "budget", "agent_stuck"]
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
    ended_by: EndReason
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


class Conversation:
    """Uma conversa em andamento, um turno do cliente por vez.

    O benchmark (`run_conversation`) e a demo jogável, em que o cliente é uma pessoa, usam esta mesma classe.
    Assim a demo julga exatamente como a avaliação.
    """

    def __init__(
        self,
        scenario: Scenario,
        agent: Agent,
        *,
        defense: Defense = Defense.STANDARD,
        max_turns: int = 8,
        max_steps: int = 6,
    ) -> None:
        self.scenario, self.agent, self.defense = scenario, agent, defense
        self.max_turns, self.max_steps = max_turns, max_steps
        self.sector = get_sector(scenario.sector)
        self.state = self.sector.initial_state(scenario.state)
        self.tools = self.sector.tool_schemas()
        self.history: list[dict[str, Any]] = [
            {"role": "system", "content": agent_system_prompt(scenario, defense)}
        ]
        self.messages: list[Message] = []
        self.events: list[CallEvent] = []
        self.stats: list[AgentCallStat] = []
        self.dialogue: list[tuple[str, str]] = []
        self.ended_by: EndReason = "max_turns"
        self.turn = 0
        self.done = False

    def customer_says(self, raw: str) -> list[Message]:
        """Recebe a fala do cliente, deixa o agente responder (com as ferramentas que ele quiser) e
        devolve as mensagens novas deste turno."""
        if self.done:
            raise RuntimeError("a conversa já terminou")
        self.turn += 1
        before = len(self.messages)
        # O cliente só pode ir embora depois de o agente responder ao menos uma vez. No piloto, um
        # simulador encerrava já na primeira mensagem, e a conversa acabava sem atendimento.
        agent_spoke = any(role == "agent" for role, _ in self.dialogue)
        finished = END_TOKEN in raw and agent_spoke
        text = raw.replace(END_TOKEN, "").strip()
        if text:
            self.messages.append(Message(turn=self.turn, role="customer", content=text))
            self.dialogue.append(("customer", text))
        if finished or not text:
            self.end("customer")
            return self.messages[before:]
        content = text + (REMINDER if self.defense == Defense.REINFORCED else "")
        self.history.append({"role": "user", "content": content})
        try:
            escalated, answered = self._agent_turn()
        except BudgetExceeded:
            self.end("budget")
            return self.messages[before:]
        if escalated:
            self.end("escalated")
        elif not answered:
            self.end("agent_stuck")
        elif self.turn >= self.max_turns:
            self.end("max_turns")
        return self.messages[before:]

    def end(self, reason: EndReason) -> None:
        self.ended_by, self.done = reason, True

    def _agent_turn(self) -> tuple[bool, bool]:
        """O agente age até responder em texto. Devolve (transferiu para humano, respondeu)."""
        turn = self.turn
        for _ in range(self.max_steps):
            reply = self.agent.respond(self.history, self.tools)
            self.stats.append(
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
                self.history.append({"role": "assistant", "content": final})
                self.messages.append(Message(turn=turn, role="agent", content=final))
                self.dialogue.append(("agent", final))
                return False, True
            self.history.append(
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
            escalated = False
            for tc in reply.tool_calls:
                args = _parse(tc.arguments)
                self.events.append(CallEvent(turn=turn, name=tc.name, arguments=args))
                result, valid = execute(self.sector, self.state, self.scenario.session, tc.name, args)
                recorded.append(
                    {
                        "name": tc.name,
                        "arguments": args if args is not None else tc.arguments,
                        "valid": valid,
                    }
                )
                self.history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
                if result is ESCALATION_RESULT:
                    escalated = True
                    break
            self.messages.append(
                Message(turn=turn, role="agent", content=reply.content or "", tool_calls=recorded)
            )
            for rec, msg in zip(recorded, self.history[-len(recorded) :], strict=False):
                self.messages.append(
                    Message(turn=turn, role="tool", name=rec["name"], content=json.loads(msg["content"]))
                )
            if escalated:
                return True, False
        return False, False

    def record(self, *, model_id: str, run: int = 1) -> ConversationRecord:
        """Julga a conversa até onde ela foi e devolve o registro completo."""
        asked_human = any(HUMAN_REQUEST.search(t) for r, t in self.dialogue if r == "customer")
        report = verify(self.scenario, self.events, customer_asked_human=asked_human)
        scenario = self.scenario
        return ConversationRecord(
            scenario_id=scenario.id,
            model_id=model_id,
            defense=self.defense,
            run=run,
            sector=scenario.sector,
            situation=scenario.situation,
            tactic=scenario.tactic,
            legit=scenario.legit,
            split=scenario.split,
            messages=self.messages,
            agent_history=self.history,
            calls=[{"turn": e.turn, "name": e.name, "arguments": e.arguments} for e in self.events],
            ended_by=self.ended_by,
            n_turns=self.turn,
            agent_stats=self.stats,
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
    """O benchmark: o cliente simulado fala, o agente responde, até alguém encerrar ou acabarem os turnos."""
    conv = Conversation(scenario, agent, defense=defense, max_turns=max_turns, max_steps=max_steps)
    while not conv.done:
        try:
            text = customer.next_message(conv.dialogue)
        except BudgetExceeded:
            conv.turn += 1
            conv.end("budget")
            break
        conv.customer_says(text)
    return conv.record(model_id=model_id, run=run)
