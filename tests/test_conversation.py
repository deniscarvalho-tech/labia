"""O laço de conversa, o cliente de LLM com cache, o filtro duplo e a avaliação, sem GPU nenhuma."""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from labia.agents import LLMAgent, ScriptedAgent, ScriptedCustomer, clean_customer_text
from labia.contracts.common import Defense, MetricName, Split, Tactic, Verdict
from labia.conversation import Conversation, ConversationRecord, run_conversation
from labia.dataset import filter_records, rejection_reasons, to_sft_example
from labia.evaluate import ModelSpec, build_audit, build_metrics, build_replay, find_row
from labia.llm import (
    BudgetExceeded,
    CachedClient,
    ChatRequest,
    ChatResponse,
    RawToolCall,
    extract_text_tool_calls,
)
from labia.prompts import REINFORCEMENT, REMINDER, agent_system_prompt, policy_text
from labia.scenarios.generator import Counts, generate
from labia.scenarios.model import Scenario

SCENARIOS = generate("test", Counts(test_per_cell=1, test_heldout_per_cell=1))


def _run(s: Scenario, policy: str, run: int = 1, defense: Defense = Defense.STANDARD) -> ConversationRecord:
    agent = ScriptedAgent(s, policy, random.Random(f"{s.id}{run}"))  # type: ignore[arg-type]
    return run_conversation(s, agent, ScriptedCustomer(s), model_id=policy, run=run, defense=defense)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
def test_ideal_agent_is_always_correct(scenario: Scenario) -> None:
    rec = _run(scenario, "ideal")
    assert rec.correct, (rec.verdict, rec.reasons)
    assert rec.process_ok
    assert rejection_reasons(rec) == []


def test_gullible_agent_lets_every_scam_through() -> None:
    frauds = [_run(s, "gullible") for s in SCENARIOS if not s.legit]
    assert all(r.verdict == Verdict.FRAUD_PASSED for r in frauds)
    assert all("processo_errado" in rejection_reasons(r) for r in frauds)


def test_rigid_agent_blocks_honest_customers() -> None:
    honest = [_run(s, "rigid") for s in SCENARIOS if s.legit]
    assert all(r.verdict == Verdict.FRICTION_DENIED for r in honest)


class FakeClient:
    """Um "modelo" que devolve respostas prontas, em ordem."""

    def __init__(self, replies: list[ChatResponse]) -> None:
        self.replies = replies
        self.requests: list[ChatRequest] = []

    def complete(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        return self.replies[min(len(self.requests) - 1, len(self.replies) - 1)]


def _scenario(situation: str, legit: bool) -> Scenario:
    return next(
        s for s in SCENARIOS if s.situation == situation and s.legit is legit and s.tactic == Tactic.NONE
    )


def test_invalid_json_arguments_count_as_invalid_calls() -> None:
    s = _scenario("D2-nao-entregue", legit=False)
    client = FakeClient(
        [
            ChatResponse(content="", tool_calls=[RawToolCall("c1", "consultar_pedido", "{id_pedido: QTI")]),
            ChatResponse(content="Não consegui consultar agora."),
        ]
    )
    rec = run_conversation(s, LLMAgent(client, "falso"), ScriptedCustomer(s), model_id="falso", max_turns=1)
    assert rec.n_calls == 1
    assert rec.n_valid_calls == 0
    tool_msg = next(m for m in rec.agent_history if m["role"] == "tool")
    assert "JSON" in tool_msg["content"]


def test_reinforced_defense_adds_reminder_and_checklist() -> None:
    s = _scenario("D2-nao-entregue", legit=False)
    client = FakeClient([ChatResponse(content="Vou verificar.")])
    run_conversation(
        s,
        LLMAgent(client, "falso"),
        ScriptedCustomer(s),
        model_id="falso",
        max_turns=1,
        defense=Defense.REINFORCED,
    )
    sent = client.requests[0].messages
    assert "Antes de qualquer ação, confira" in sent[0]["content"]
    assert sent[-1]["role"] == "user"
    assert sent[-1]["content"].endswith(REMINDER)


def test_reinforcement_never_mentions_the_heldout_tactic() -> None:
    """Para não favorecer ninguém na tática nova, o reforço não fala de pedidos fatiados nem de somar.

    A política em si menciona limites somados (B5, D3) e vale para todos os modelos; o teste olha só o
    texto que o reforço acrescenta.
    """
    s = _scenario("D2-nao-entregue", legit=False)
    added = agent_system_prompt(s, Defense.REINFORCED).replace(
        agent_system_prompt(s, Defense.STANDARD)[:-80], ""
    )
    text = (REINFORCEMENT + added + REMINDER).lower()
    assert not any(word in text for word in ("fatia", "fracion", "soma", "acumul", "um de cada vez"))


def test_tool_calls_written_inside_the_text_are_recovered() -> None:
    text, calls = extract_text_tool_calls(
        'Vou checar.\n<tool_call>{"name": "consultar_pedido", "arguments": {"id_pedido": "QTI-1"}}</tool_call>'
    )
    assert text == "Vou checar."
    assert calls[0].name == "consultar_pedido"
    assert json.loads(calls[0].arguments) == {"id_pedido": "QTI-1"}


def test_cache_returns_the_same_answer_without_calling_again(tmp_path: Path) -> None:
    inner = FakeClient([ChatResponse(content="oi")])
    cached = CachedClient(inner, tmp_path)
    req = ChatRequest(model="m", messages=[{"role": "user", "content": "x"}], seed=1)
    assert cached.complete(req).content == "oi"
    again = cached.complete(req)
    assert again.cached
    assert len(inner.requests) == 1
    cached.complete(ChatRequest(model="m", messages=[{"role": "user", "content": "x"}], seed=2))
    assert len(inner.requests) == 2  # outra semente é outra rodada


def test_budget_cap_stops_the_round(tmp_path: Path) -> None:
    cached = CachedClient(FakeClient([ChatResponse(content="oi")]), tmp_path, max_calls=1)
    cached.complete(ChatRequest(model="m", messages=[{"role": "user", "content": "a"}]))
    with pytest.raises(BudgetExceeded):
        cached.complete(ChatRequest(model="m", messages=[{"role": "user", "content": "b"}]))


def test_simulator_text_cleanup() -> None:
    assert clean_customer_text('"Cliente: quero meu dinheiro\nAtendente: claro"') == "quero meu dinheiro"


def test_sft_export_uses_standard_prompt_and_strips_reminders() -> None:
    s = _scenario("D2-nao-entregue", legit=True)
    rec = _run(s, "ideal", defense=Defense.REINFORCED)
    example = to_sft_example(rec, s)
    assert example["messages"][0]["content"] == agent_system_prompt(s, Defense.STANDARD)
    assert all(REMINDER not in str(m.get("content")) for m in example["messages"])
    assert example["messages"][-1]["role"] != "user"
    assert {t["function"]["name"] for t in example["tools"]} >= {"reembolsar", "consultar_pedido"}


def test_filter_keeps_only_right_answers_with_right_process() -> None:
    records = [_run(s, "ideal") for s in SCENARIOS] + [_run(s, "gullible") for s in SCENARIOS if not s.legit]
    kept, reasons = filter_records(records)
    assert all(r.model_id == "ideal" for r in kept)
    assert reasons["resultado_errado"] > 0


def test_policy_prompt_matches_the_approved_document() -> None:
    for sector, doc in [("bank", "politica-banco-saracura.md"), ("delivery", "politica-quati-delivery.md")]:
        text = Path(f"docs/especificacao/{doc}").read_text(encoding="utf-8").replace("\r\n", "\n")
        marker = "## Parte 1. Texto que o agente recebe\n"
        part1 = text[text.index(marker) + len(marker) : text.index("\n---\n\n## Parte 2")].strip() + "\n"
        assert policy_text(sector).replace("\r\n", "\n") == part1


def test_metrics_end_to_end_with_scripted_agents() -> None:
    records = [_run(s, p, run) for p in ("gullible", "rigid") for s in SCENARIOS for run in (1, 2, 3)]
    models = [ModelSpec(p, p, None, None, "n/a", "self_hosted") for p in ("gullible", "rigid")]
    metrics = build_metrics(records, models, is_sample=True, release="v0", resamples=200)
    gullible = find_row(metrics, "gullible", MetricName.FRAUD_RATE, Split.ALL_TEST)
    rigid = find_row(metrics, "rigid", MetricName.FRICTION_RATE, Split.ALL_TEST)
    assert gullible is not None
    assert gullible.value == 1.0
    assert rigid is not None
    assert rigid.value == 1.0
    assert any(c.model_id == "gullible" for c in metrics.curves)
    replay = build_replay(records, metrics, focus=("gullible", "rigid"))
    assert replay.conversations
    # Todo cenário escolhido aparece em todos os modelos, para o replay comparar lado a lado.
    by_scenario: dict[str, set[str]] = {}
    for conv in replay.conversations:
        by_scenario.setdefault(conv.scenario_id, set()).add(conv.model_id)
    model_ids = {r.model_id for r in records}
    assert all(found == model_ids for found in by_scenario.values())
    # Os cenários em que o crédulo e o rígido discordam entram (até o limite de 40).
    first = {(r.model_id, r.scenario_id): r.verdict for r in records if r.run == 1}
    disagreements = sorted(s.id for s in SCENARIOS if first[("gullible", s.id)] != first[("rigid", s.id)])
    assert set(disagreements[:40]) <= set(by_scenario)
    audit = build_audit(records, metrics, focus_model="gullible", resamples=200, seed=0)
    assert audit.findings
    assert all(f.severity in ("low", "medium", "high", "critical") for f in audit.findings)


class FirstMessageQuits:
    """Um simulador que, como o Qwen no piloto, encerra já na primeira mensagem."""

    def __init__(self) -> None:
        self.calls = 0

    def next_message(self, history: list[tuple[str, str]]) -> str:
        self.calls += 1
        return "Quero meu reembolso agora. [FIM]" if self.calls == 1 else "Ok, obrigado. [FIM]"


def test_customer_cannot_leave_before_the_agent_answers() -> None:
    s = _scenario("D2-nao-entregue", legit=True)
    rec = run_conversation(s, ScriptedAgent(s, "ideal"), FirstMessageQuits(), model_id="x")
    assert any(m.role == "agent" for m in rec.messages)
    assert rec.n_turns == 2


def test_filter_rejects_conversation_without_agent_turn() -> None:
    s = _scenario("D2-nao-entregue", legit=False)
    rec = _run(s, "ideal")
    silent = rec.model_copy(update={"messages": [m for m in rec.messages if m.role == "customer"]})
    assert "agente_nao_respondeu" in rejection_reasons(silent)


def test_hypotheses_detect_a_scripted_improvement() -> None:
    """Crédulo como "base" e ideal como "sft": H1 e H3 confirmadas, e o atrito não piora (H2)."""
    from labia.report import evaluate_hypotheses, inject, render_results

    records = []
    for s in SCENARIOS:
        for run in (1, 2, 3):
            records.append(_run(s, "gullible", run).model_copy(update={"model_id": "base"}))
            records.append(_run(s, "ideal", run).model_copy(update={"model_id": "sft"}))
    results = {h.id: h for h in evaluate_hypotheses(records, resamples=500)}
    assert results["H1"].rejected_after_holm
    assert results["H1"].difference < 0
    assert results["H3"].rejected_after_holm
    assert results["H2"].rejected_after_holm  # o ideal não barra ninguém
    models = [ModelSpec(m, m, None, None, "n/a", "self_hosted") for m in ("base", "sft")]
    metrics = build_metrics(records, models, is_sample=False, release="v0", resamples=200)
    honest = next(s.id for s in SCENARIOS if s.legit and s.tactic != Tactic.SPLIT_REQUEST)
    sensitivity = {h.id: h for h in evaluate_hypotheses(records, resamples=500, exclude=frozenset({honest}))}
    assert sensitivity["H2"].n_pairs == results["H2"].n_pairs - 3  # as 3 rodadas do cenário excluído
    assert sensitivity["H1"].n_pairs == results["H1"].n_pairs
    section = render_results(metrics, list(results.values()), list(sensitivity.values()), 1)
    assert "H1" in section
    assert "Táticas vistas" in section
    assert "Análise de sensibilidade" in section
    readme = "antes\n<!-- RESULTADOS:INICIO -->\nvelho\n<!-- RESULTADOS:FIM -->\ndepois"
    updated = inject(readme, section)
    assert "velho" not in updated
    assert updated.startswith("antes")
    assert updated.endswith("depois")


def test_rate_limit_spaces_requests() -> None:
    from labia.llm import RateLimitedClient

    now = [0.0]
    slept: list[float] = []

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        now[0] += seconds

    client = RateLimitedClient(
        FakeClient([ChatResponse(content="ok")]), rpm=30, clock=lambda: now[0], sleep=sleep
    )
    for _ in range(3):
        client.complete(ChatRequest(model="m", messages=[]))
    assert slept == [2.0, 2.0]  # 30 por minuto = um pedido a cada 2 segundos


@pytest.mark.parametrize("policy", ["ideal", "gullible", "rigid", "noisy"])
def test_turn_by_turn_conversation_matches_the_benchmark(policy: str) -> None:
    """A demo jogável (uma pessoa digitando, um turno por vez) julga igual ao benchmark."""
    for s in SCENARIOS[:12]:
        bench = _run(s, policy)
        agent = ScriptedAgent(s, policy, random.Random(f"{s.id}1"))  # type: ignore[arg-type]
        customer = ScriptedCustomer(s)
        conv = Conversation(s, agent)
        while not conv.done:
            conv.customer_says(customer.next_message(conv.dialogue))
        live = conv.record(model_id=policy)
        assert live.model_dump() == bench.model_dump()


def test_finished_conversation_refuses_more_messages() -> None:
    s = SCENARIOS[0]
    conv = Conversation(s, ScriptedAgent(s, "ideal", random.Random(0)))
    conv.end("customer")
    with pytest.raises(RuntimeError):
        conv.customer_says("oi")
