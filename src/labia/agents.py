"""Quem conversa na sandbox: o agente (o atendente) e o cliente simulado.

Cada um tem duas versões. A de LLM é a usada no piloto, no treino e na avaliação. A roteirizada segue
regras fixas e serve para testar o laço de conversa sem GPU e para gerar os dados de exemplo do painel
(sempre marcados com is_sample). Nenhum número publicado sai de um agente roteirizado.
"""

from __future__ import annotations

import json
import random
import re
from typing import Any, Literal, Protocol

from labia.contracts.common import Tactic
from labia.llm import ChatClient, ChatRequest, ChatResponse, RawToolCall
from labia.prompts import SIMULATOR_KICKOFF, simulator_system_prompt
from labia.sandbox import get_sector
from labia.sandbox.core import ToolCall
from labia.scenarios.model import Action, Scenario


class Agent(Protocol):
    def respond(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ChatResponse: ...


class Customer(Protocol):
    def next_message(self, history: list[tuple[str, str]]) -> str:
        """history: pares (papel, texto), com papel "customer" ou "agent"."""
        ...


# ---------------------------------------------------------------------- versões com LLM


class LLMAgent:
    def __init__(
        self,
        client: ChatClient,
        model: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        seed: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.client, self.model = client, model
        self.temperature, self.max_tokens, self.seed, self.extra = temperature, max_tokens, seed, extra

    def respond(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ChatResponse:
        return self.client.complete(
            ChatRequest(
                model=self.model,
                messages=list(messages),  # cópia: o laço continua alterando a lista depois
                tools=tools,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                seed=self.seed,
                extra=self.extra,
            )
        )


class LLMCustomer:
    def __init__(
        self,
        client: ChatClient,
        model: str,
        scenario: Scenario,
        *,
        temperature: float = 0.9,
        max_tokens: int = 400,
        seed: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.client, self.model, self.seed, self.temperature = client, model, seed, temperature
        self.max_tokens, self.extra = max_tokens, extra
        self.system = simulator_system_prompt(scenario)

    def next_message(self, history: list[tuple[str, str]]) -> str:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system},
            {"role": "user", "content": SIMULATOR_KICKOFF},
        ]
        for role, text in history:
            messages.append({"role": "assistant" if role == "customer" else "user", "content": text})
        response = self.client.complete(
            ChatRequest(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                seed=self.seed,
                extra=self.extra,
            )
        )
        return clean_customer_text(response.content)


_SPEAKER_PREFIX = re.compile(r"^\s*(cliente|eu|customer)\s*:\s*", re.IGNORECASE)


def clean_customer_text(text: str) -> str:
    """Tira o que o simulador às vezes acrescenta: "Cliente:" no começo, aspas e a fala do atendente."""
    text = text.strip().strip('"').strip()
    text = _SPEAKER_PREFIX.sub("", text)
    for marker in ("\nAtendente:", "\nAssistente:", "\nAgente:"):
        if marker in text:
            text = text.split(marker)[0]
    return text.strip()


# ---------------------------------------------------------------------- versões roteirizadas

ScriptedPolicy = Literal["ideal", "gullible", "rigid", "noisy"]
DONE_MARK = "Pronto"


class ScriptedAgent:
    """Agente de regras fixas.

    ideal: consulta, concede o que é permitido, transfere quando a política manda, nega o resto.
    gullible: faz o que o cliente pede, sem consultar. rigid: consulta e nega tudo.
    noisy: às vezes consulta, às vezes cede à pressão, às vezes nega por engano. Serve para os dados de
    exemplo terem números intermediários e curvas de resistência com formato.
    """

    def __init__(
        self,
        scenario: Scenario,
        policy: ScriptedPolicy,
        rng: random.Random | None = None,
        p_check: float = 0.7,
        p_resist: float = 0.75,
        p_serve: float = 0.85,
    ) -> None:
        self.scenario, self.policy = scenario, policy
        self.rng = rng or random.Random(0)
        self.p_check, self.p_resist, self.p_serve = p_check, p_resist, p_serve
        self.sector = get_sector(scenario.sector)
        self.state = self.sector.initial_state(scenario.state)
        self.done: set[int] = set()
        self.pending_text = ""
        self.counter = 0
        self.checked = False

    def _call(self, name: str, args: dict[str, Any]) -> RawToolCall:
        self.counter += 1
        return RawToolCall(
            id=f"call_{self.counter}", name=name, arguments=json.dumps(args, ensure_ascii=False)
        )

    def _reads(self, action: Action) -> list[RawToolCall]:
        call = self.sector.validate(ToolCall(action.tool, dict(action.arguments)))
        reads = []
        for tool, target in self.sector.required_reads(call, self.scenario.session):
            arg = {"id_pedido": target} if tool == "consultar_pedido" else {"cpf": self.scenario.session.cpf}
            reads.append(self._call(tool, arg))
        if self.scenario.tactic == Tactic.FAKE_PRIOR_PROMISE:
            reads.append(self._call("consultar_protocolos", {"cpf": self.scenario.session.cpf}))
        return reads

    def respond(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ChatResponse:
        if messages[-1]["role"] == "tool":
            return ChatResponse(content=self.pending_text)
        turn = sum(1 for m in messages if m["role"] == "user")
        goals = self.scenario.goal_actions
        index = min(turn - 1, len(goals) - 1) if self.scenario.tactic == Tactic.SPLIT_REQUEST else 0
        if index in self.done or not goals:
            return ChatResponse(content="Posso ajudar em mais alguma coisa?")
        action = goals[index]
        call = self.sector.validate(ToolCall(action.tool, dict(action.arguments)))
        allowed = self.sector.assess(self.state, self.scenario.session, call).allowed

        calls: list[RawToolCall] = []
        wants_check = self.policy in ("ideal", "rigid") or (
            self.policy == "noisy" and self.rng.random() < self.p_check
        )
        if wants_check and not self.checked:
            calls.extend(self._reads(action))
            self.checked = True

        decision = self._decide(allowed)
        if decision == "act":
            calls.append(self._call(action.tool, dict(action.arguments)))
            self.sector.apply(self.state, self.scenario.session, call)
            self.done.add(index)
            text = f"{DONE_MARK}, resolvido."
        elif decision == "escalate":
            calls.append(
                self._call("escalar_para_humano", {"motivo": "a política manda transferir este caso"})
            )
            text = "Vou transferir você para a equipe responsável."
        else:
            text = "Sinto muito, mas pela nossa política não consigo fazer isso."
        if calls:
            self.pending_text = text
            return ChatResponse(content="", tool_calls=calls)
        return ChatResponse(content=text)

    def _decide(self, allowed: bool) -> str:
        mandated = self.scenario.escalation_mandated
        if self.policy == "gullible":
            return "act"
        if self.policy == "rigid":
            return "escalate" if mandated else "deny"
        if self.policy == "ideal":
            if allowed:
                return "act"
            return "escalate" if mandated else "deny"
        if allowed:
            return "act" if self.rng.random() < self.p_serve else "deny"
        if self.rng.random() < self.p_resist:
            return "escalate" if mandated and self.rng.random() < 0.7 else "deny"
        return "act"


class ScriptedCustomer:
    """Cliente de regras fixas: pede, insiste duas vezes se for negado e encerra."""

    def __init__(self, scenario: Scenario, insist: int = 2) -> None:
        self.scenario, self.insist = scenario, insist
        self.step, self.denials = 0, 0

    def next_message(self, history: list[tuple[str, str]]) -> str:
        steps = self.scenario.customer.steps or (self.scenario.customer.goal,)
        if not history:
            return f"Olá. {steps[0]}"
        last_agent = next((text for role, text in reversed(history) if role == "agent"), "")
        if last_agent.startswith(DONE_MARK):
            self.step += 1
            self.denials = 0
            if self.step < len(steps):
                return steps[self.step]
            return "Obrigado! [FIM]"
        self.denials += 1
        if self.denials > self.insist or "transferir" in last_agent:
            return "Tudo bem. [FIM]"
        return f"Por favor, eu preciso muito disso. {steps[self.step]}"
