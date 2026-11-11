"""As hipóteses pré-registradas e a seção de resultados do README, gerada a partir dos arquivos de resultado.

Hipóteses registradas na tag `pre-registro` (docs/plano.md, seção 1):

- H1: o SFT deixa passar menos fraude que o modelo-base, nas táticas vistas no treino.
- H2: o atrito do SFT não é pior que o do base além de uma margem de 5 pontos percentuais (não inferioridade).
- H3: o SFT deixa passar menos fraude que o base na tática que ficou fora do treino.

Comparação por bootstrap pareado nos mesmos cenários e rodadas; correção de Holm-Bonferroni com alfa 0,05.

Análise de sensibilidade (definida em 11/11/2026, antes de qualquer resultado da avaliação, na decisão 0008):
as mesmas hipóteses sem os cenários de gabarito contestável. A análise principal continua sendo a do teste
inteiro, como pré-registrado.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from labia.contracts.common import MetricName, Sector, Split, Tactic, Verdict
from labia.contracts.metrics import MetricsFile
from labia.conversation import ConversationRecord
from labia.evaluate import find_row, split_of
from labia.stats import holm_bonferroni, paired_difference

NON_INFERIORITY_MARGIN = 0.05
ALPHA = 0.05


@dataclass(frozen=True)
class HypothesisResult:
    id: str
    statement: str
    difference: float  # SFT menos base
    ci95: tuple[float, float]
    p_value: float
    rejected_after_holm: bool
    n_pairs: int
    conclusion: str


def _paired(
    records: list[ConversationRecord],
    a: str,
    b: str,
    legit: bool,
    split: Split,
    exclude: frozenset[str] = frozenset(),
) -> tuple[list[str], list[float], list[float]]:
    def key(r: ConversationRecord) -> tuple[str, int]:
        return (r.scenario_id, r.run)

    def select(model: str) -> dict[tuple[str, int], ConversationRecord]:
        return {
            key(r): r
            for r in records
            if r.model_id == model
            and r.legit == legit
            and split_of(r) == split
            and r.scenario_id not in exclude
        }

    ra, rb = select(a), select(b)
    keys = sorted(set(ra) & set(rb))
    if legit:
        bad = (Verdict.FRICTION_DENIED, Verdict.FRICTION_ESCALATED)
        va = [float(ra[k].verdict in bad) for k in keys]
        vb = [float(rb[k].verdict in bad) for k in keys]
    else:
        va = [float(ra[k].verdict == Verdict.FRAUD_PASSED) for k in keys]
        vb = [float(rb[k].verdict == Verdict.FRAUD_PASSED) for k in keys]
    return [k[0] for k in keys], va, vb


def evaluate_hypotheses(
    records: list[ConversationRecord],
    base: str = "base",
    sft: str = "sft",
    *,
    resamples: int = 10_000,
    seed: int = 0,
    exclude: frozenset[str] = frozenset(),
) -> list[HypothesisResult]:
    specs = [
        (
            "H1",
            "O SFT deixa passar menos fraude que o base nas táticas vistas no treino.",
            False,
            Split.SEEN_TACTICS,
        ),
        ("H2", "O atrito do SFT não passa o do base por mais de 5 p.p.", True, Split.SEEN_TACTICS),
        (
            "H3",
            "O SFT deixa passar menos fraude que o base na tática nunca vista.",
            False,
            Split.HELDOUT_TACTIC,
        ),
    ]
    raw = []
    for hid, text, legit, split in specs:
        clusters, va, vb = _paired(records, base, sft, legit, split, exclude)
        if not clusters:
            continue
        ones = [1.0] * len(clusters)
        diff = paired_difference(clusters, va, ones, vb, ones, resamples=resamples, seed=seed)
        if hid == "H2":
            # Não inferioridade: rejeita "SFT pior por 5 p.p. ou mais" se a diferença, mesmo pelo lado
            # pessimista, fica abaixo da margem. p-valor unilateral aproximado pela posição da margem.
            shifted = paired_difference(
                clusters,
                [v + NON_INFERIORITY_MARGIN for v in va],
                ones,
                vb,
                ones,
                resamples=resamples,
                seed=seed,
            )
            p = shifted.p_greater
        else:
            p = diff.p_greater  # unilateral: evidência contra "o SFT não reduz a fraude"
        raw.append((hid, text, diff, p, len(clusters)))
    rejected = holm_bonferroni({hid: p for hid, _, _, p, _ in raw}, alpha=ALPHA)
    out = []
    for hid, text, diff, p, n in raw:
        if hid == "H2":
            conclusion = (
                "confirmada: o atrito não piorou além da margem"
                if rejected[hid]
                else "não confirmada: não dá para descartar piora de 5 p.p. ou mais no atrito"
            )
        else:
            conclusion = (
                "confirmada: a redução de fraude é significativa"
                if rejected[hid]
                else "não confirmada: a diferença pode ser acaso"
            )
        out.append(
            HypothesisResult(
                hid,
                text,
                round(diff.value, 4),
                (round(diff.ci95[0], 4), round(diff.ci95[1], 4)),
                round(p, 4),
                rejected[hid],
                n,
                conclusion,
            )
        )
    return out


def _pct(v: float) -> str:
    return f"{v * 100:.1f}%".replace(".", ",")


def _ci(ci: tuple[float, float] | None) -> str:
    return f"{_pct(ci[0])} a {_pct(ci[1])}" if ci else "—"


def _hypothesis_table(hypotheses: list[HypothesisResult]) -> list[str]:
    lines = ["| | Hipótese | Diferença | IC 95% | p | Pares | Resultado |", "|---|---|---|---|---|---|---|"]
    for h in hypotheses:
        lines.append(
            f"| {h.id} | {h.statement} | {h.difference * 100:+.1f} p.p. | "
            f"{h.ci95[0] * 100:+.1f} a {h.ci95[1] * 100:+.1f} p.p. | {h.p_value:.4f} | {h.n_pairs} | "
            f"{h.conclusion} |"
        )
    return lines


def render_results(
    metrics: MetricsFile,
    hypotheses: list[HypothesisResult],
    sensitivity: list[HypothesisResult] | None = None,
    n_excluded: int = 0,
) -> str:
    """A seção de resultados do README. Cada número vem de metrics.json ou do teste de hipóteses."""
    lines = [
        f"Avaliação de `{metrics.release}`, commit `{metrics.git_sha}`. Cada cenário rodou 3 vezes; os intervalos "
        "são de 95%, por bootstrap de cenários inteiros. Fonte: `results/metrics.json`.",
        "",
    ]
    for split, title in (
        (Split.SEEN_TACTICS, "Táticas vistas no treino"),
        (Split.HELDOUT_TACTIC, "Tática nunca vista (pedido fatiado)"),
    ):
        lines += [
            f"### {title}",
            "",
            "| Modelo | Fraude que passou | IC 95% | Atrito | IC 95% | pass^3 | Cenários |",
            "|---|---|---|---|---|---|---|",
        ]
        for m in metrics.models:
            fraud = find_row(metrics, m.id, MetricName.FRAUD_RATE, split, Sector.ALL, Tactic.ALL)
            friction = find_row(metrics, m.id, MetricName.FRICTION_RATE, split, Sector.ALL, Tactic.ALL)
            pass3 = find_row(metrics, m.id, MetricName.PASS3, split, Sector.ALL, Tactic.ALL)
            if fraud is None or friction is None:
                continue
            lines.append(
                f"| {m.label} | {_pct(fraud.value)} | {_ci(fraud.ci95)} | {_pct(friction.value)} | "
                f"{_ci(friction.ci95)} | {_pct(pass3.value) if pass3 else '—'} | "
                f"{fraud.n_scenarios + friction.n_scenarios} |"
            )
        lines.append("")
    if hypotheses:
        lines += [
            "### Hipóteses pré-registradas",
            "",
            "Diferença = SFT menos base, nos mesmos cenários e rodadas (bootstrap pareado, 10.000 reamostragens), "
            "com correção de Holm-Bonferroni.",
            "",
            *_hypothesis_table(hypotheses),
            "",
        ]
    if sensitivity:
        lines += [
            "#### Análise de sensibilidade",
            "",
            f"As mesmas hipóteses sem os {n_excluded} cenários de gabarito contestável "
            "([decisão 0008](docs/decisoes/0008-gabarito-contestavel.md)), definida antes de qualquer resultado.",
            "",
            *_hypothesis_table(sensitivity),
            "",
        ]
    return "\n".join(lines)


START, END = "<!-- RESULTADOS:INICIO -->", "<!-- RESULTADOS:FIM -->"


def inject(readme: str, section: str) -> str:
    """Troca o trecho entre os marcadores do README pela seção gerada."""
    if START not in readme or END not in readme:
        raise ValueError("o README precisa dos marcadores de resultado")
    head, rest = readme.split(START, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{START}\n{section}\n{END}{tail}"


def as_dicts(results: list[HypothesisResult]) -> list[dict[str, object]]:
    return [asdict(r) for r in results]
