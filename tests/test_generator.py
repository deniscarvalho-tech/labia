"""Propriedades do gerador de cenários: determinismo, divisão sem vazamento e o teste cruzado."""

from __future__ import annotations

import json
import re

import pytest

from labia.contracts.common import Tactic, Verdict
from labia.scenarios.fake import fake_cpf, is_valid_cpf
from labia.scenarios.generator import Counts, generate
from labia.scenarios.model import Scenario
from labia.scenarios.tactics import HELDOUT_TACTIC
from labia.verifier import assess_goal

SMALL = Counts(train_per_cell=2, test_per_cell=1, test_heldout_per_cell=2)


@pytest.fixture(scope="module")
def train() -> list[Scenario]:
    return generate("train", SMALL)


@pytest.fixture(scope="module")
def test_set() -> list[Scenario]:
    return generate("test", SMALL)


def test_same_seed_same_scenarios() -> None:
    a = [s.model_dump(mode="json") for s in generate("train", SMALL)]
    b = [s.model_dump(mode="json") for s in generate("train", SMALL)]
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_different_base_seed_changes_scenarios() -> None:
    a = generate("train", SMALL)[0]
    b = generate("train", SMALL, base_seed=1)[0]
    assert a.state != b.state


def test_cross_check_generator_and_verifier(train: list[Scenario], test_set: list[Scenario]) -> None:
    """O teste cruzado: fazer o que o golpista pede viola a regra da situação; fazer o que o honesto pede, não."""
    for s in [*train, *test_set]:
        report = assess_goal(s)
        if s.legit:
            assert report.verdict == Verdict.SERVED_CORRECTLY, (s.id, report.reasons)
        else:
            assert report.verdict == Verdict.FRAUD_PASSED, s.id
            assert s.rule in report.violated_rules, (s.id, report.violated_rules)
            assert report.value_at_risk > 0, s.id


def test_every_tactic_has_both_sides(train: list[Scenario]) -> None:
    sides: dict[tuple[str, str], set[bool]] = {}
    for s in train:
        sides.setdefault((s.situation, s.tactic), set()).add(s.legit)
    assert all(v == {True, False} for v in sides.values())


def test_heldout_tactic_never_in_train(train: list[Scenario], test_set: list[Scenario]) -> None:
    assert all(s.tactic != HELDOUT_TACTIC for s in train)
    assert any(s.tactic == HELDOUT_TACTIC for s in test_set)


def test_train_and_test_share_no_identifiers(train: list[Scenario], test_set: list[Scenario]) -> None:
    pattern = re.compile(r"\b(?:QTI|TAR|CMP|PIX)-\d+\b")

    def ids(scenarios: list[Scenario]) -> set[str]:
        return {m for s in scenarios for m in pattern.findall(json.dumps(s.state))}

    assert ids(train).isdisjoint(ids(test_set))
    assert {s.id for s in train}.isdisjoint({s.id for s in test_set})


def test_all_cpfs_are_invalid_by_construction(train: list[Scenario]) -> None:
    cpf_pattern = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
    found = {m for s in train for m in cpf_pattern.findall(json.dumps(s.model_dump(mode="json")))}
    assert found
    assert not any(is_valid_cpf(c) for c in found)


def test_cpf_check_digit_algorithm() -> None:
    """Monta um CPF válido em memória (nunca escrito no código) e confere que o algoritmo o reconhece."""
    from labia.scenarios.fake import _check_digit

    base = [3, 1, 4, 1, 5, 9, 2, 6, 5]
    first = _check_digit(base)
    second = _check_digit([*base, first])
    valid = "".join(map(str, [*base, first, second]))
    assert is_valid_cpf(valid)
    assert not is_valid_cpf(valid[:-1] + str((int(valid[-1]) + 1) % 10))
    assert not is_valid_cpf("111.111.111-11")


@pytest.mark.parametrize("seed", range(50))
def test_fake_cpf_never_valid(seed: int) -> None:
    import random

    assert not is_valid_cpf(fake_cpf(random.Random(seed)))


def test_promise_scenarios_carry_a_protocol(train: list[Scenario]) -> None:
    for s in train:
        if s.tactic != Tactic.FAKE_PRIOR_PROMISE:
            continue
        number = s.customer.facts["protocolo"]
        registered = [p["numero"] for p in s.state.get("protocolos", [])]
        if s.legit:
            assert number in registered
            assert not s.escalation_mandated


def test_customer_never_sees_the_system_state(train: list[Scenario]) -> None:
    """O cliente simulado recebe só o que um cliente saberia: nada de flags internos do sistema."""
    internal = (
        "cobranca_indevida",
        "embalagem_conferida",
        "dispositivo_cadastrado",
        "limite_max_preaprovado",
    )
    for s in train:
        text = json.dumps(s.customer.model_dump(), ensure_ascii=False)
        assert not any(flag in text for flag in internal), s.id
