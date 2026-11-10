"""Do professor ao dado de treino: o filtro duplo e a exportação no formato de SFT.

Uma conversa só entra no treino se tiver o resultado certo E o processo certo (consultou antes de agir,
transferiu quando devia, checou promessas). Além disso, não pode ter sinal da tática que ficou fora do
treino nem um simulador que saiu do personagem. O objetivo é o aluno aprender a verificar, e não a
acertar por sorte (decisão 5 do plano).
"""

from __future__ import annotations

import copy
import re
from collections import Counter
from typing import Any

from labia.contracts.common import Defense, Tactic
from labia.conversation import ConversationRecord
from labia.prompts import REMINDER, agent_system_prompt
from labia.sandbox import get_sector
from labia.scenarios.model import Scenario

BENEFIT_TOOLS = frozenset(
    {
        "reembolsar",
        "emitir_cupom",
        "estornar_tarifa",
        "ajustar_limite",
        "cancelar_pedido",
        "abrir_contestacao",
        "desbloquear_conta",
        "alterar_endereco",
    }
)

#: Sinais de que o cliente simulado saiu do personagem.
OUT_OF_CHARACTER = re.compile(
    r"(como (uma )?ia\b|sou (uma )?(ia|intelig[eê]ncia artificial)|modelo de linguagem|esta simula[cç][aã]o|"
    r"\bsimula[cç][aã]o\b|^\s*(atendente|assistente|agente)\s*:|\[(?!FIM\]))",
    re.IGNORECASE | re.MULTILINE,
)


def benefit_actions(rec: ConversationRecord) -> int:
    return sum(1 for c in rec.calls if c["name"] in BENEFIT_TOOLS and c["arguments"] is not None)


def is_contaminated(rec: ConversationRecord) -> bool:
    """Detector determinístico de fracionamento (T5) fora do teste: duas ou mais ações de benefício.

    Nas táticas de treino o cliente pede uma coisa só. Se o agente concedeu duas vezes, é provável que o
    simulador tenha fatiado o pedido por conta própria, e a conversa ensinaria a tática que precisa ficar
    de fora para medirmos a generalização.
    """
    return rec.tactic != Tactic.SPLIT_REQUEST and benefit_actions(rec) >= 2


def out_of_character(rec: ConversationRecord) -> bool:
    customer = [str(m.content) for m in rec.messages if m.role == "customer"]
    return not customer or any(OUT_OF_CHARACTER.search(t) for t in customer)


def rejection_reasons(rec: ConversationRecord) -> list[str]:
    reasons = []
    if not rec.correct:
        reasons.append("resultado_errado")
    if not rec.process_ok:
        reasons.append("processo_errado")
    if rec.n_valid_calls != rec.n_calls:
        reasons.append("chamada_invalida")
    if rec.ended_by in ("budget", "agent_stuck"):
        reasons.append("fim_anormal")
    if is_contaminated(rec):
        reasons.append("contaminacao_t5")
    if out_of_character(rec):
        reasons.append("simulador_fora_do_personagem")
    return reasons


def to_sft_example(rec: ConversationRecord, scenario: Scenario) -> dict[str, Any]:
    """Exporta a conversa como exemplo de SFT, com destilação de contexto.

    O professor atendeu com o prompt reforçado; o exemplo guarda o prompt padrão e tira os lembretes.
    Assim o aluno aprende a agir como se tivesse o reforço, sem pagar por esses tokens em cada chamada.
    """
    messages = copy.deepcopy(rec.agent_history)
    messages[0] = {"role": "system", "content": agent_system_prompt(scenario, Defense.STANDARD)}
    for m in messages:
        if m["role"] == "user":
            m["content"] = m["content"].replace(REMINDER, "")
    answered = {m.get("tool_call_id") for m in messages if m["role"] == "tool"}
    for m in messages:
        if m["role"] == "assistant" and m.get("tool_calls"):
            m["tool_calls"] = [tc for tc in m["tool_calls"] if tc["id"] in answered]
    while messages and messages[-1]["role"] == "user":
        messages.pop()
    return {
        "id": f"{rec.scenario_id}-r{rec.run}",
        "messages": messages,
        "tools": get_sector(scenario.sector).tool_schemas(),
        "meta": {
            "scenario_id": rec.scenario_id,
            "sector": rec.sector,
            "situation": rec.situation,
            "tactic": rec.tactic.value,
            "legit": rec.legit,
            "verdict": rec.verdict.value,
            "teacher": rec.model_id,
        },
    }


def filter_records(records: list[ConversationRecord]) -> tuple[list[ConversationRecord], Counter[str]]:
    kept, reasons = [], Counter[str]()
    for rec in records:
        why = rejection_reasons(rec)
        reasons.update(why)
        if not why:
            kept.append(rec)
    return kept, reasons
