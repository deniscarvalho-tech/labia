"""A estatística confere com contas feitas à mão e com propriedades conhecidas."""

from __future__ import annotations

import pytest

from labia.stats import (
    holm_bonferroni,
    kaplan_meier,
    kaplan_meier_bootstrap,
    paired_difference,
    pass_hat_k,
    ratio_bootstrap,
)


def test_ratio_point_estimate_is_pooled() -> None:
    est = ratio_bootstrap(["a", "a", "b"], [1, 0, 1], [1, 1, 1], resamples=500)
    assert est.value == pytest.approx(2 / 3)
    assert est.n_clusters == 2
    assert est.n_obs == 3
    assert est.ci95 is not None
    assert est.ci95[0] <= est.value <= est.ci95[1]


def test_cluster_bootstrap_is_wider_than_pretending_runs_are_independent() -> None:
    """Rodadas idênticas dentro do cenário: tratar como independentes subestima a incerteza."""
    scenarios = [f"s{i}" for i in range(30)]
    outcome = [1.0 if i % 3 == 0 else 0.0 for i in range(30)]
    clustered = ratio_bootstrap(
        [s for s in scenarios for _ in range(3)],
        [o for o in outcome for _ in range(3)],
        [1.0] * 90,
        resamples=3000,
        seed=1,
    )
    naive = ratio_bootstrap(
        [f"r{i}" for i in range(90)],
        [o for o in outcome for _ in range(3)],
        [1.0] * 90,
        resamples=3000,
        seed=1,
    )
    assert clustered.ci95 is not None
    assert naive.ci95 is not None
    width = clustered.ci95[1] - clustered.ci95[0]
    assert width > 1.4 * (naive.ci95[1] - naive.ci95[0])


def test_bootstrap_is_reproducible() -> None:
    args = (["a", "b", "c", "d"], [1, 0, 1, 1], [1, 1, 1, 1])
    assert ratio_bootstrap(*args, seed=7) == ratio_bootstrap(*args, seed=7)


def test_paired_difference_detects_a_clear_improvement() -> None:
    clusters = [f"s{i}" for i in range(40)]
    a = [1.0] * 30 + [0.0] * 10  # modelo A deixa passar 75%
    b = [1.0] * 5 + [0.0] * 35  # modelo B deixa passar 12,5%
    diff = paired_difference(clusters, a, [1.0] * 40, b, [1.0] * 40, resamples=3000)
    assert diff.value == pytest.approx(-0.625)
    assert diff.ci95[1] < 0
    assert diff.p_two_sided < 0.01


def test_holm_bonferroni_is_step_down() -> None:
    result = holm_bonferroni({"H1": 0.001, "H2": 0.04, "H3": 0.02}, alpha=0.05)
    assert result == {"H1": True, "H3": True, "H2": True}
    result = holm_bonferroni({"H1": 0.001, "H2": 0.04, "H3": 0.03}, alpha=0.05)
    assert result["H1"] is True  # 0,001 <= 0,05/3
    assert result["H3"] is False  # 0,03 > 0,05/2: aqui o procedimento para
    assert result["H2"] is False  # mesmo com 0,04 < 0,05, nada depois de uma falha é rejeitado
    assert holm_bonferroni({"H1": 0.03, "H2": 0.04}, alpha=0.05) == {"H1": False, "H2": False}


def test_pass_hat_k() -> None:
    assert pass_hat_k([(3, 3), (2, 3), (0, 3)]) == pytest.approx(1 / 3)
    assert pass_hat_k([(4, 5)], k=3) == pytest.approx(4 / 10)  # C(4,3)/C(5,3)


def test_kaplan_meier_by_hand() -> None:
    # 4 golpes: cede no turno 1; cede no 2; conversa acaba no 2 sem ceder (censura); cede no 3.
    curve = kaplan_meier([1, 2, 2, 3], [True, True, False, True], max_turn=3)
    assert curve[0] == 1.0
    assert curve[1] == pytest.approx(3 / 4)
    assert curve[2] == pytest.approx(3 / 4 * (1 - 1 / 3))
    assert curve[3] == pytest.approx(0.0)


def test_kaplan_meier_without_events_stays_at_one() -> None:
    assert kaplan_meier([3, 5, 8], [False, False, False], max_turn=8) == [1.0] * 9


def test_kaplan_meier_bootstrap_brackets_the_curve() -> None:
    clusters = [f"s{i // 2}" for i in range(20)]
    durations = [1 + (i % 4) for i in range(20)]
    events = [i % 3 != 0 for i in range(20)]
    points = kaplan_meier_bootstrap(clusters, durations, events, max_turn=4, resamples=300)
    for value, ci in points[1:]:
        assert ci is not None
        assert ci[0] - 1e-9 <= value <= ci[1] + 1e-9
