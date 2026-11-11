"""Os gráficos do README, a partir de results/metrics.json e experiments/06-treino-sft/treino.json.

Cada gráfico sai em duas versões (tema claro e escuro), e o README escolhe pela preferência de quem lê. As
cores são as mesmas do painel (validadas para daltonismo), e cada modelo tem a cor da posição dele na lista
do contrato, como no painel. Recusa dado de exemplo, salvo com --exemplo e uma pasta fora do repositório.

    uv run --with matplotlib python scripts/graficos.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent

THEMES: dict[str, dict[str, Any]] = {
    "claro": {
        "page": "#fcfcfb",
        "ink1": "#0b0b0b",
        "ink2": "#52514e",
        "ink3": "#6f6d68",
        "grid": "#e1e0d9",
        "axis": "#c3c2b7",
        "series": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
    },
    "escuro": {
        "page": "#1a1a19",
        "ink1": "#f0efec",
        "ink2": "#c3c2b7",
        "ink3": "#9d9b94",
        "grid": "#2c2c2a",
        "axis": "#383835",
        "series": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
    },
}
TACTICS = [
    ("none", "sem tática"),
    ("authority", "autoridade"),
    ("institutional_threat", "ameaça institucional"),
    ("urgency_emotion", "urgência e emoção"),
    ("fake_prior_promise", "promessa anterior"),
    ("split_request", "pedido fatiado\n(fora do treino)"),
]


def style(ax: Any, t: dict[str, Any]) -> None:
    ax.set_facecolor(t["page"])
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(t["axis"])
    ax.tick_params(colors=t["ink2"], labelsize=9)
    ax.grid(True, color=t["grid"], linewidth=0.75)
    ax.set_axisbelow(True)
    ax.xaxis.label.set_color(t["ink2"])
    ax.yaxis.label.set_color(t["ink2"])


def figure(t: dict[str, Any], w: float, h: float, title: str, subtitle: str) -> tuple[Any, Any]:
    fig, ax = plt.subplots(figsize=(w, h), dpi=100)
    fig.patch.set_facecolor(t["page"])
    fig.text(0.02, 0.97, title, color=t["ink1"], fontsize=13, fontweight="bold", va="top")
    fig.text(0.02, 0.91, subtitle, color=t["ink3"], fontsize=9.5, va="top")
    style(ax, t)
    return fig, ax


def legend(fig: Any, ax: Any, t: dict[str, Any], max_cols: int) -> int:
    """Legenda numa faixa abaixo do subtítulo, fora da área dos dados. Devolve quantas linhas ocupou."""
    handles, labels = ax.get_legend_handles_labels()
    width = sum(len(lb) + 6 for lb in labels)
    ncol = max_cols if width <= 105 else min(2, max_cols)
    fig.legend(
        handles,
        labels,
        loc="upper left",
        bbox_to_anchor=(0.015, 0.875),
        ncol=ncol,
        frameon=False,
        fontsize=8.5,
        labelcolor=t["ink2"],
        handletextpad=0.4,
        columnspacing=1.4,
    )
    return -(-len(labels) // ncol)


def row(
    metrics: dict[str, Any], model: str, metric: str, split: str, tactic: str = "all"
) -> dict[str, Any] | None:
    for r in metrics["rows"]:
        if (r["model_id"], r["metric"], r["split"], r["sector"], r["tactic"]) == (
            model,
            metric,
            split,
            "all",
            tactic,
        ):
            return r
    return None


def pct_axis(axis: Any) -> None:
    axis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v * 100:.0f}%"))


def color(metrics: dict[str, Any], t: dict[str, Any], model: str) -> str:
    ids = [m["id"] for m in metrics["models"]]
    return str(t["series"][ids.index(model) % 8])


def label(metrics: dict[str, Any], model: str) -> str:
    return next(str(m["label"]) for m in metrics["models"] if m["id"] == model)


def fraud_friction(metrics: dict[str, Any], t: dict[str, Any], out: Path) -> None:
    fig, ax = figure(
        t,
        8,
        5.6,
        "Fraude × atrito, táticas vistas no treino",
        "Cada ponto é um modelo; as barras são intervalos de 95% por bootstrap de cenários. Melhor: embaixo à esquerda.",
    )
    placed: list[tuple[float, float]] = []
    top = 0.0
    for m in metrics["models"]:
        fraud = row(metrics, m["id"], "fraud_rate", "seen_tactics")
        fric = row(metrics, m["id"], "friction_rate", "seen_tactics")
        if not fraud or not fric:
            continue
        c = color(metrics, t, m["id"])
        ax.errorbar(
            fric["value"],
            fraud["value"],
            xerr=[[fric["value"] - fric["ci95"][0]], [fric["ci95"][1] - fric["value"]]],
            yerr=[[fraud["value"] - fraud["ci95"][0]], [fraud["ci95"][1] - fraud["value"]]],
            fmt="o",
            color=c,
            markersize=8,
            markeredgecolor=t["page"],
            markeredgewidth=1.5,
            elinewidth=1,
            capsize=0,
            label=m["label"],
            zorder=3,
        )
        top = max(top, fraud["ci95"][1])
        right = fric["value"] > 0.7
        # Rótulo de um ponto vizinho a outro já rotulado vai para baixo, para os textos não se sobreporem.
        crowded = any(abs(fric["value"] - x) < 0.15 and abs(fraud["value"] - y) < 0.06 for x, y in placed)
        placed.append((fric["value"], fraud["value"]))
        ax.annotate(
            m["label"],
            (fric["value"], fraud["value"]),
            xytext=(-7 if right else 7, -14 if crowded else 6),
            textcoords="offset points",
            ha="right" if right else "left",
            fontsize=8.5,
            color=t["ink1"],
        )
    ax.set_xlabel("Atrito: clientes honestos barrados")
    ax.set_ylabel("Fraude que passou")
    pct_axis(ax.xaxis)
    pct_axis(ax.yaxis)
    ax.set_xlim(-0.03, max(1.0, ax.get_xlim()[1]) + 0.03)
    ax.set_ylim(-0.02, min(1.0, max(0.4, top + 0.08)))
    rows = legend(fig, ax, t, max_cols=2)
    fig.subplots_adjust(top=0.8 - 0.035 * rows, left=0.1, right=0.97, bottom=0.11)
    fig.savefig(out, facecolor=t["page"])
    plt.close(fig)


def fraud_by_tactic(metrics: dict[str, Any], t: dict[str, Any], out: Path, models: list[str]) -> None:
    fig, ax = figure(
        t,
        8,
        5.2,
        "Fraude que passou, por tática",
        "Intervalos de 95% por bootstrap de cenários. O pedido fatiado nunca apareceu no treino.",
    )
    ys = list(range(len(TACTICS)))[::-1]
    offsets = {m: (i - (len(models) - 1) / 2) * 0.22 for i, m in enumerate(models)}
    for model in models:
        c = color(metrics, t, model)
        first = True
        for (tactic, _), y in zip(TACTICS, ys, strict=True):
            split = "heldout_tactic" if tactic == "split_request" else "seen_tactics"
            r = row(metrics, model, "fraud_rate", split, tactic)
            if not r:
                continue
            yy = y + offsets[model]
            ax.plot([r["ci95"][0], r["ci95"][1]], [yy, yy], color=c, linewidth=1.5, solid_capstyle="round")
            ax.plot(
                r["value"],
                yy,
                "o",
                color=c,
                markersize=8,
                markeredgecolor=t["page"],
                markeredgewidth=1.5,
                label=label(metrics, model) if first else None,
                zorder=3,
            )
            first = False
    ax.set_yticks(ys, [name for _, name in TACTICS])
    ax.axhline(0.5, color=t["axis"], linewidth=1, linestyle=(0, (3, 3)))
    ax.set_xlabel("Fraude que passou")
    pct_axis(ax.xaxis)
    ax.set_xlim(-0.02, 1.02)
    ax.grid(False, axis="y")
    rows = legend(fig, ax, t, max_cols=3)
    fig.subplots_adjust(top=0.83 - 0.04 * rows, left=0.24, right=0.97, bottom=0.11)
    fig.savefig(out, facecolor=t["page"])
    plt.close(fig)


def resistance(metrics: dict[str, Any], t: dict[str, Any], out: Path, models: list[str]) -> None:
    fig, ax = figure(
        t,
        8,
        4.8,
        "Resistência à insistência",
        "Fração dos golpes que o agente ainda não tinha concedido, turno a turno (Kaplan–Meier, faixa de 95%).",
    )
    for model in models:
        curve = next(
            (c for c in metrics["curves"] if c["model_id"] == model and c["split"] == "all_test"), None
        )
        if not curve:
            continue
        c = color(metrics, t, model)
        turns = [p["turn"] for p in curve["points"]]
        ax.step(
            turns,
            [p["value"] for p in curve["points"]],
            where="post",
            color=c,
            linewidth=2,
            label=label(metrics, model),
        )
        ax.fill_between(
            turns,
            [p["ci95"][0] for p in curve["points"]],
            [p["ci95"][1] for p in curve["points"]],
            step="post",
            color=c,
            alpha=0.15,
            linewidth=0,
        )
    ax.set_xlabel("Turno da conversa")
    ax.set_ylabel("Golpes ainda resistidos")
    pct_axis(ax.yaxis)
    ax.set_ylim(0, 1.02)
    rows = legend(fig, ax, t, max_cols=3)
    fig.subplots_adjust(top=0.81 - 0.045 * rows, left=0.1, right=0.97, bottom=0.13)
    fig.savefig(out, facecolor=t["page"])
    plt.close(fig)


def training_loss(log: list[dict[str, Any]], t: dict[str, Any], out: Path) -> None:
    fig, ax = figure(
        t,
        8,
        3.8,
        "Perda do treino (Lábia v0)",
        "Perda média a cada 5 passos, só nas falas do agente. Perda baixa não prova segurança: quem decide é o teste.",
    )
    ax.plot([h["epoch"] for h in log], [h["loss"] for h in log], color=t["series"][2], linewidth=2)
    ax.set_xlabel("Época")
    ax.set_ylabel("Perda")
    ax.set_ylim(bottom=0)
    fig.subplots_adjust(top=0.78, left=0.1, right=0.97, bottom=0.16)
    fig.savefig(out, facecolor=t["page"])
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--metrics", default="results/metrics.json")
    p.add_argument("--treino", default="experiments/06-treino-sft/treino.json")
    p.add_argument("--out", default="docs/img")
    p.add_argument("--modelos", nargs="+", default=["base", "base+reforco", "sft"])
    p.add_argument(
        "--exemplo", action="store_true", help="aceita dado de exemplo (só para testar, fora do repo)"
    )
    args = p.parse_args()
    metrics = json.loads((ROOT / args.metrics).read_text(encoding="utf-8"))
    out = Path(args.out)
    if metrics["is_sample"] and not args.exemplo:
        sys.exit("results/metrics.json é de exemplo: os gráficos do README só saem com resultado real")
    out.mkdir(parents=True, exist_ok=True)
    known = [m["id"] for m in metrics["models"]]
    models = [m for m in args.modelos if m in known] or known[:3]
    training = ROOT / args.treino
    for theme, t in THEMES.items():
        plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
        fraud_friction(metrics, t, out / f"fraude-atrito-{theme}.svg")
        fraud_by_tactic(metrics, t, out / f"fraude-por-tatica-{theme}.svg", models)
        resistance(metrics, t, out / f"resistencia-{theme}.svg", models)
        if training.exists():
            log = [h for h in json.loads(training.read_text(encoding="utf-8"))["log"] if "loss" in h]
            training_loss(log, t, out / f"perda-treino-{theme}.svg")
    print(f"gráficos em {out}: {sorted(f.name for f in out.glob('*.svg'))}")


if __name__ == "__main__":
    main()
