"""O raio-x da geração: onde o professor acerta e erra, e o que sobrou para o treino.

Lê as conversas cruas da geração (todas as tentativas) e devolve um dicionário com as contagens que vão
para experiments/04-geracao/analise.json. As taxas do professor usam só a primeira tentativa de cada
cenário, porque as seguintes existem justamente por causa das falhas e enviesariam a conta.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from labia.contracts.common import Verdict
from labia.conversation import ConversationRecord
from labia.dataset import rejection_reasons
from labia.scenarios.model import Scenario, is_contested

#: O agente escreve que fez (ou vai fazer agora) uma ação de benefício. Heurística por expressão regular:
#: serve para medir o padrão "anunciou sem executar", não para julgar uma conversa.
CLAIMED_ACTION = re.compile(
    r"(foi|foram|está|esta|já)\s+(atualizad|alterad|estornad|reembolsad|cancelad|abert|registrad|desbloquead|"
    r"emitid|ajustad|processad|confirmad|realizad|conclu)|\b(vou|vamos)\s+(mudar|alterar|estornar|reembolsar|"
    r"cancelar|abrir|desbloquear|emitir|ajustar|processar)|(confirmado|concluído|realizado)!|em andamento",
    re.IGNORECASE,
)
#: Raciocínio interno do professor vazado em inglês na resposta ao cliente.
REASONING_LEAK = re.compile(
    r"\b(We need|Need to|The user|Let's|We should|We must|We can't|The customer|Also need|So we)\b"
)


def approved(records: list[ConversationRecord]) -> list[ConversationRecord]:
    """A primeira conversa aprovada de cada cenário, como o notebook de geração exporta."""
    kept, seen = [], set()
    for r in sorted(records, key=lambda r: (r.scenario_id, r.run)):
        if r.scenario_id not in seen and not rejection_reasons(r):
            kept.append(r)
            seen.add(r.scenario_id)
    return kept


def claimed_without_action(rec: ConversationRecord) -> bool:
    """Cliente honesto negado, nenhuma ação de benefício executada, e o agente disse que fez."""
    return (
        rec.legit
        and rec.verdict == Verdict.FRICTION_DENIED
        and rec.n_benefit_actions == 0
        and any(
            m.role == "agent" and isinstance(m.content, str) and CLAIMED_ACTION.search(m.content)
            for m in rec.messages
        )
    )


def leaked_reasoning(rec: ConversationRecord) -> bool:
    return any(
        m.role == "agent" and isinstance(m.content, str) and REASONING_LEAK.search(m.content)
        for m in rec.messages
    )


def _rate(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def summarize_generation(records: list[ConversationRecord], scenarios: dict[str, Scenario]) -> dict[str, Any]:
    first = [r for r in records if r.run == 1]
    kept = approved(records)
    fraud = [r for r in first if not r.legit]
    honest = [r for r in first if r.legit]
    friction = (Verdict.FRICTION_DENIED, Verdict.FRICTION_ESCALATED)

    by_cell: dict[str, Counter[str]] = defaultdict(Counter)
    for r in first:
        by_cell[f"{r.tactic.value}|{'legitimo' if r.legit else 'golpe'}"][r.verdict.value] += 1
    by_situation: dict[str, Counter[str]] = defaultdict(Counter)
    for r in first:
        by_situation[f"{r.situation}|{'legitimo' if r.legit else 'golpe'}"][r.verdict.value] += 1

    def accuracy(cells: dict[str, Counter[str]]) -> dict[str, dict[str, Any]]:
        out = {}
        for key in sorted(cells):
            c = cells[key]
            n = sum(c.values())
            ok = c[Verdict.SERVED_CORRECTLY.value] + c[Verdict.FRAUD_BLOCKED.value]
            out[key] = {"n": n, "acerto": _rate(ok, n), "vereditos": dict(c)}
        return out

    honest_denied = [r for r in honest if r.verdict == Verdict.FRICTION_DENIED]
    attempts_to_approve = Counter(r.run for r in kept)
    kept_cells = Counter(f"{r.tactic.value}|{'legitimo' if r.legit else 'golpe'}" for r in kept)
    return {
        "nota": "Taxas do professor (gpt-oss-20b com o prompt reforçado) na primeira tentativa, em cenários de "
        "TREINO. Não são comparáveis às taxas do teste.",
        "cenarios": len({r.scenario_id for r in records}),
        "conversas": len(records),
        "tentativas": dict(sorted(Counter(r.run for r in records).items())),
        "aprovadas": len(kept),
        "aprovadas_na_tentativa": dict(sorted(attempts_to_approve.items())),
        "professor_primeira_tentativa": {
            "fraude_que_passou": _rate(sum(r.verdict == Verdict.FRAUD_PASSED for r in fraud), len(fraud)),
            "atrito": _rate(sum(r.verdict in friction for r in honest), len(honest)),
            "concessao_acima_do_direito": sum(r.verdict == Verdict.OVERGRANT for r in honest),
            "golpes": len(fraud),
            "legitimos": len(honest),
        },
        "legitimos_negados": {
            "total": len(honest_denied),
            "anunciou_acao_sem_executar": sum(claimed_without_action(r) for r in honest_denied),
            "metodo": "expressão regular sobre o texto do agente (CLAIMED_ACTION); heurística, revisada por amostra",
        },
        "acerto_por_tatica_e_lado": accuracy(by_cell),
        "acerto_por_situacao_e_lado": accuracy(by_situation),
        "treino_por_tatica_e_lado": dict(sorted(kept_cells.items())),
        "treino_gabarito_contestavel": sum(is_contested(scenarios[r.scenario_id]) for r in kept),
        "treino_raciocinio_vazado": sum(leaked_reasoning(r) for r in kept),
    }
