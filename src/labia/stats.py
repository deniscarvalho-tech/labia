"""Estatística das métricas: bootstrap por cenário, comparação pareada, Holm-Bonferroni e Kaplan-Meier.

Referência: Miller (2024), "Adding Error Bars to Evals", arXiv 2411.00640.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import comb

import numpy as np
from numpy.typing import NDArray

DEFAULT_RESAMPLES = 10_000


@dataclass(frozen=True)
class Estimate:
    value: float
    ci95: tuple[float, float] | None
    n_clusters: int
    n_obs: int


def _clusters(
    clusters: Sequence[str], num: Sequence[float], den: Sequence[float]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Soma numerador e denominador por cenário: cada cenário vira um "cacho" com as suas rodadas."""
    order: dict[str, int] = {}
    for c in clusters:
        order.setdefault(c, len(order))
    n = np.zeros(len(order))
    d = np.zeros(len(order))
    for c, x, y in zip(clusters, num, den, strict=True):
        n[order[c]] += x
        d[order[c]] += y
    return n, d


def ratio_bootstrap(
    clusters: Sequence[str],
    num: Sequence[float],
    den: Sequence[float],
    *,
    resamples: int = DEFAULT_RESAMPLES,
    seed: int = 0,
) -> Estimate:
    """Razão soma(num) / soma(den) com IC 95% por bootstrap de cenários inteiros.

    Reamostrar cenários (e não rodadas) importa: as 3 rodadas de um cenário se parecem entre si, e
    tratá-las como independentes daria um intervalo estreito demais.
    """
    n, d = _clusters(clusters, num, den)
    total_den = d.sum()
    if total_den == 0:
        return Estimate(float("nan"), None, len(n), len(clusters))
    value = float(n.sum() / total_den)
    if len(n) < 2:
        return Estimate(value, None, len(n), len(clusters))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(n), size=(resamples, len(n)))
    dens = d[idx].sum(axis=1)
    nums = n[idx].sum(axis=1)
    ok = dens > 0
    stats = nums[ok] / dens[ok]
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return Estimate(value, (float(lo), float(hi)), len(n), len(clusters))


@dataclass(frozen=True)
class Difference:
    """Diferença entre dois modelos nos mesmos cenários (B menos A)."""

    value: float
    ci95: tuple[float, float]
    p_two_sided: float
    p_greater: float  # P(B - A >= 0) sob a reamostragem: evidência contra "B é menor que A"


def paired_difference(
    clusters: Sequence[str],
    num_a: Sequence[float],
    den_a: Sequence[float],
    num_b: Sequence[float],
    den_b: Sequence[float],
    *,
    resamples: int = DEFAULT_RESAMPLES,
    seed: int = 0,
) -> Difference:
    """Bootstrap pareado: o mesmo sorteio de cenários vale para os dois modelos.

    Comparar nos mesmos cenários elimina a variação de "um modelo pegou cenários mais fáceis".
    Os dois lados precisam estar alinhados: a posição i é o mesmo cenário e a mesma rodada.
    """
    na, da = _clusters(clusters, num_a, den_a)
    nb, db = _clusters(clusters, num_b, den_b)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(na), size=(resamples, len(na)))
    with np.errstate(invalid="ignore", divide="ignore"):
        diffs = nb[idx].sum(1) / db[idx].sum(1) - na[idx].sum(1) / da[idx].sum(1)
    diffs = diffs[np.isfinite(diffs)]
    value = float(nb.sum() / db.sum() - na.sum() / da.sum())
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    p_le = float((diffs <= 0).mean())
    p_ge = float((diffs >= 0).mean())
    return Difference(value, (float(lo), float(hi)), min(1.0, 2 * min(p_le, p_ge)), p_ge)


def holm_bonferroni(p_values: dict[str, float], alpha: float = 0.05) -> dict[str, bool]:
    """Correção de Holm para várias hipóteses: devolve quais são rejeitadas (o efeito é significativo)."""
    ordered = sorted(p_values.items(), key=lambda kv: kv[1])
    m = len(ordered)
    rejected: dict[str, bool] = {}
    still = True
    for i, (name, p) in enumerate(ordered):
        still = still and p <= alpha / (m - i)
        rejected[name] = still
    return rejected


def pass_hat_k(correct_per_scenario: Sequence[tuple[int, int]], k: int = 3) -> float:
    """pass^k do τ-bench: média, entre os cenários, de C(c, k) / C(n, k), com c acertos em n rodadas."""
    values = [comb(c, k) / comb(n, k) for c, n in correct_per_scenario if n >= k]
    return float(np.mean(values)) if values else float("nan")


def kaplan_meier(durations: Sequence[int], events: Sequence[bool], max_turn: int) -> list[float]:
    """Curva de resistência por turno: S(k) = fração dos golpes que ainda não tinham cedido até o turno k.

    `durations` é o turno em que o agente cedeu (evento) ou o último turno observado (censura: a conversa
    acabou sem ele ceder, e não sabemos o que faria depois). Devolve S(0) a S(max_turn).
    """
    d = np.asarray(durations)
    e = np.asarray(events, dtype=bool)
    survival = [1.0]
    s = 1.0
    for k in range(1, max_turn + 1):
        at_risk = int((d >= k).sum())
        failed = int(((d == k) & e).sum())
        if at_risk > 0:
            s *= 1.0 - failed / at_risk
        survival.append(s)
    return survival


def kaplan_meier_bootstrap(
    clusters: Sequence[str],
    durations: Sequence[int],
    events: Sequence[bool],
    max_turn: int,
    *,
    resamples: int = 2_000,
    seed: int = 0,
) -> list[tuple[float, tuple[float, float] | None]]:
    """A curva de Kaplan-Meier com IC 95% por bootstrap de cenários."""
    point = kaplan_meier(durations, events, max_turn)
    groups: dict[str, list[int]] = {}
    for i, c in enumerate(clusters):
        groups.setdefault(c, []).append(i)
    keys = list(groups)
    if len(keys) < 2:
        return [(v, None) for v in point]
    rng = np.random.default_rng(seed)
    curves = np.empty((resamples, max_turn + 1))
    d = np.asarray(durations)
    e = np.asarray(events, dtype=bool)
    for b in range(resamples):
        chosen = rng.integers(0, len(keys), size=len(keys))
        rows = [i for j in chosen for i in groups[keys[j]]]
        curves[b] = kaplan_meier(d[rows].tolist(), e[rows].tolist(), max_turn)
    lo = np.percentile(curves, 2.5, axis=0)
    hi = np.percentile(curves, 97.5, axis=0)
    return [(point[k], (float(lo[k]), float(hi[k]))) for k in range(max_turn + 1)]
