"""Linha de comando da Lábia: `labia <comando>`. O Makefile chama estes comandos."""

from __future__ import annotations

import argparse
import json
import os
import random
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from labia.contracts import export_schemas
from labia.contracts.common import Defense, Kind, MetricName, Split
from labia.contracts.summary import HeadlineCard
from labia.contracts.versions import Version, VersionLinks, VersionsFile
from labia.scenarios.generator import Counts, dump_jsonl, generate, load_jsonl

DATA = Path("data")


def write_json(path: Path, model: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((model.model_dump_json(indent=2) + "\n").encode("utf-8"))


def cmd_schemas(_: argparse.Namespace) -> None:
    for path in export_schemas(Path("schemas")):
        print(f"escrito {path}")


def cmd_scenarios(args: argparse.Namespace) -> None:
    counts = Counts(args.train_per_cell, args.test_per_cell, args.test_heldout_per_cell)
    manifest: dict[str, object] = {"base_seed": args.seed, "counts": counts.__dict__, "files": {}}
    for split in ("train", "test"):
        scenarios = generate(split, counts, base_seed=args.seed)
        path = DATA / "scenarios" / f"{split}.jsonl"
        digest = dump_jsonl(scenarios, path)
        by_tactic = Counter(s.tactic for s in scenarios)
        by_side = Counter("legitimo" if s.legit else "golpe" for s in scenarios)
        manifest["files"][split] = {  # type: ignore[index]
            "path": str(path).replace("\\", "/"),
            "sha256": digest,
            "n": len(scenarios),
            "by_tactic": dict(sorted(by_tactic.items())),
            "by_side": dict(sorted(by_side.items())),
        }
        print(f"{split}: {len(scenarios)} cenários em {path} (sha256 {digest[:12]}…)")
    Path("scenarios-manifest.json").write_bytes(
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    print("manifesto em scenarios-manifest.json: ele congela o conjunto de teste")


def cmd_run(args: argparse.Namespace) -> None:
    """Roda conversas com modelos de verdade, por qualquer servidor compatível com a API da OpenAI."""
    from labia.agents import LLMAgent, LLMCustomer
    from labia.llm import CachedClient, OpenAICompatClient
    from labia.runner import Job, run_batch, run_seed

    scenarios = load_jsonl(Path(args.scenarios))
    if args.ids:
        wanted = set(Path(args.ids).read_text(encoding="utf-8").split())
        scenarios = [s for s in scenarios if s.id in wanted]
    if args.limit:
        scenarios = scenarios[: args.limit]
    cache = Path(args.cache_dir)
    agent_client = CachedClient(
        OpenAICompatClient(args.agent_url, os.environ.get(args.agent_key_env, "sem-chave")),
        cache / "agent",
        max_calls=args.max_calls,
    )
    sim_client = CachedClient(
        OpenAICompatClient(args.sim_url, os.environ.get(args.sim_key_env, "sem-chave")),
        cache / "sim",
        max_calls=args.max_calls,
    )
    jobs = [Job(s, r) for s in scenarios for r in range(1, args.runs + 1)]
    print(f"{len(jobs)} conversas: {len(scenarios)} cenários × {args.runs} rodadas")
    run_batch(
        jobs,
        lambda s, r: LLMAgent(
            agent_client, args.agent_model, temperature=args.temperature, seed=run_seed(s, r, "agent")
        ),
        lambda s, r: LLMCustomer(sim_client, args.sim_model, s, seed=run_seed(s, r, "customer")),
        Path(args.out),
        model_id=args.model_id,
        defense=Defense(args.defense),
        workers=args.workers,
        max_turns=args.max_turns,
    )
    print(
        f"chamadas novas: agente {agent_client.calls_made}, simulador {sim_client.calls_made}; "
        f"do cache: {agent_client.cache_hits + sim_client.cache_hits}"
    )


def cmd_filter(args: argparse.Namespace) -> None:
    """Aplica o filtro duplo e exporta o dataset de SFT."""
    from labia.dataset import filter_records, to_sft_example
    from labia.runner import load_records

    records = load_records(*map(Path, args.runs))
    scenarios = {s.id: s for s in load_jsonl(Path(args.scenarios))}
    kept, reasons = filter_records(records)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as fh:
        for rec in kept:
            fh.write(
                (
                    json.dumps(to_sft_example(rec, scenarios[rec.scenario_id]), ensure_ascii=False) + "\n"
                ).encode()
            )
    print(f"aprovadas {len(kept)} de {len(records)} ({len(kept) / max(1, len(records)):.0%})")
    for reason, n in reasons.most_common():
        print(f"  reprovadas por {reason}: {n}")


def cmd_samples(args: argparse.Namespace) -> None:
    """Gera results/*.json de EXEMPLO rodando agentes roteirizados no pipeline de verdade.

    Os números são de agentes de regras fixas, não de modelos. Por isso tudo sai com is_sample: true, os
    modelos se chamam "exemplo-..." e o script de publicação recusa esses arquivos.
    """
    from labia.agents import ScriptedAgent, ScriptedCustomer
    from labia.conversation import run_conversation
    from labia.evaluate import CardSpec, ModelSpec, build_audit, build_metrics, build_replay, build_summary

    scenarios = generate("test", Counts(test_per_cell=1, test_heldout_per_cell=4))
    lineup = [
        (
            ModelSpec(
                "exemplo-credulo", "Exemplo: agente crédulo (roteirizado)", None, None, "n/a", "self_hosted"
            ),
            "gullible",
            {},
        ),
        (
            ModelSpec(
                "exemplo-ruidoso", "Exemplo: agente ruidoso (roteirizado)", None, None, "n/a", "self_hosted"
            ),
            "noisy",
            {"p_check": 0.6, "p_resist": 0.7},
        ),
        (
            ModelSpec(
                "exemplo-cauteloso",
                "Exemplo: agente cauteloso (roteirizado)",
                None,
                None,
                "n/a",
                "self_hosted",
                Defense.REINFORCED,
            ),
            "noisy",
            {"p_check": 0.95, "p_resist": 0.93, "p_serve": 0.8},
        ),
        (
            ModelSpec(
                "exemplo-rigido", "Exemplo: agente rígido (roteirizado)", None, None, "n/a", "self_hosted"
            ),
            "rigid",
            {},
        ),
    ]
    records = []
    for spec, policy, params in lineup:
        for s in scenarios:
            for run in (1, 2, 3):
                rng = random.Random(f"{spec.id}|{s.id}|{run}")
                agent = ScriptedAgent(s, policy, rng, **params)  # type: ignore[arg-type]
                records.append(
                    run_conversation(
                        s, agent, ScriptedCustomer(s), model_id=spec.id, run=run, defense=spec.defense
                    )
                )
    models = [spec for spec, _, _ in lineup]
    metrics = build_metrics(records, models, is_sample=True, release="v0", resamples=args.resamples)
    note = "DADOS DE EXEMPLO de agentes roteirizados."
    cards = [
        CardSpec(
            "fraud_rate_exemplo",
            "Fraude que passou",
            "exemplo-cauteloso",
            MetricName.FRAUD_RATE,
            Split.SEEN_TACTICS,
            "exemplo-ruidoso",
            "agente ruidoso",
            note,
        ),
        CardSpec(
            "friction_rate_exemplo",
            "Clientes honestos barrados",
            "exemplo-cauteloso",
            MetricName.FRICTION_RATE,
            Split.SEEN_TACTICS,
            "exemplo-ruidoso",
            "agente ruidoso",
            note,
        ),
        CardSpec(
            "fraud_rate_heldout_exemplo",
            "Fraude na tática nunca vista",
            "exemplo-cauteloso",
            MetricName.FRAUD_RATE,
            Split.HELDOUT_TACTIC,
            "exemplo-ruidoso",
            "agente ruidoso",
            note,
        ),
    ]
    cost = HeadlineCard(
        id="cost_per_1k_exemplo",
        label="Custo por mil conversas",
        model_id="exemplo-cauteloso",
        value=0.0,
        unit="usd",
        ci95=None,
        kind=Kind.ESTIMATED,
        assumptions="Dado de exemplo: o custo real sai do benchmark de vazão na GPU, com o preço "
        "público da GPU por hora e a data da consulta.",
        note=note,
    )
    summary = build_summary(metrics, cards, extra=[cost])
    replay = build_replay(records, metrics, focus=("exemplo-ruidoso", "exemplo-cauteloso"))
    audit = build_audit(records, metrics, focus_model="exemplo-ruidoso", resamples=args.resamples, seed=0)
    versions = VersionsFile(
        is_sample=True,
        generated_at=datetime.now(UTC),
        versions=[
            Version(
                version="v0",
                date=date(2026, 11, 14),
                title="SFT com destilação filtrada pelo verificador",
                status="in_progress",
                changes=["Dado de exemplo: a lista real sai do script de release."],
                headline=summary.headline[:2],
                links=VersionLinks(github_release=None),
            ),
        ],
    )
    write_json(Path("results/metrics.json"), metrics)
    write_json(Path("results/summary.json"), summary)
    write_json(Path("results/replay.json"), replay)
    write_json(Path("results/audit_findings.json"), audit)
    write_json(Path("site-data/versions.json"), versions)
    print(
        f"{len(records)} conversas roteirizadas; {len(metrics.rows)} linhas de métricas; "
        f"{len(replay.conversations)} conversas no replay; {len(audit.findings)} achados de auditoria"
    )
    print("tudo com is_sample: true")


def cmd_publish_check(_: argparse.Namespace) -> None:
    """Recusa a publicação se algum arquivo do contrato for de exemplo ou não validar."""
    from labia.contracts import CONTRACT_FILES, validate_file

    problems = []
    for published in CONTRACT_FILES:
        path = Path(published)
        if not path.exists():
            problems.append(f"{published}: não existe")
            continue
        model = validate_file(published, path)
        if getattr(model, "is_sample", True):
            problems.append(f"{published}: is_sample é true (dado de exemplo não é publicado)")
    if problems:
        print("publicação recusada:")
        for problem in problems:
            print(f"  - {problem}")
        raise SystemExit(1)
    print("ok: todos os arquivos validam e nenhum é de exemplo")


def cmd_evaluate(args: argparse.Namespace) -> None:
    """Das conversas julgadas da avaliação aos results/*.json reais (is_sample: false)."""
    from labia.contracts.audit import Retest
    from labia.contracts.common import Verdict
    from labia.evaluate import CardSpec, ModelSpec, build_audit, build_metrics, build_replay, build_summary
    from labia.report import as_dicts, evaluate_hypotheses
    from labia.runner import load_records
    from labia.scenarios.model import is_contested

    records = load_records(*map(Path, args.runs))
    present = {r.model_id for r in records}
    config = json.loads(Path(args.models).read_text(encoding="utf-8"))
    models = [
        ModelSpec(
            c["id"],
            c["label"],
            c["base_model"],
            c["params_b"],
            c["license"],
            c["access"],
            Defense(c["defense"]),
        )
        for c in config
        if c["id"] in present
    ]
    unknown = present - {m.id for m in models}
    if unknown:
        raise SystemExit(f"modelos sem entrada em {args.models}: {sorted(unknown)}")
    metrics = build_metrics(records, models, is_sample=False, release=args.release, resamples=args.resamples)
    note = "Bootstrap de cenários inteiros."
    cards = [
        CardSpec(
            "fraud_rate_sft_vs_base",
            "Fraude que passou",
            args.focus,
            MetricName.FRAUD_RATE,
            Split.SEEN_TACTICS,
            args.baseline,
            "modelo-base",
            f"Táticas vistas no treino. {note}",
        ),
        CardSpec(
            "friction_rate_sft_vs_base",
            "Clientes honestos barrados",
            args.focus,
            MetricName.FRICTION_RATE,
            Split.SEEN_TACTICS,
            args.baseline,
            "modelo-base",
            f"Táticas vistas no treino. {note}",
        ),
        CardSpec(
            "fraud_rate_heldout_sft_vs_base",
            "Fraude na tática nunca vista",
            args.focus,
            MetricName.FRAUD_RATE,
            Split.HELDOUT_TACTIC,
            args.baseline,
            "modelo-base",
            f"Pedido fatiado, fora do treino. {note}",
        ),
    ]
    summary = build_summary(metrics, cards)
    replay = build_replay(records, metrics, focus=(args.baseline, args.focus))
    audit = build_audit(records, metrics, focus_model=args.baseline, resamples=args.resamples, seed=0)
    retested = []
    for finding in audit.findings:
        rule = finding.rule_ids[0]
        again = [
            r
            for r in records
            if r.model_id == args.focus and not r.legit and r.situation.split("-")[0] == rule
        ]
        if again:
            rate = sum(r.verdict == Verdict.FRAUD_PASSED for r in again) / len(again)
            status = "fixed" if rate <= args.fixed_threshold else "still_failing"
            finding = finding.model_copy(update={"retest": Retest(status=status, version=args.release)})
        retested.append(finding)
    audit = audit.model_copy(update={"findings": retested})
    hypotheses = evaluate_hypotheses(records, args.baseline, args.focus, resamples=args.resamples)
    contested = frozenset(s.id for s in generate("test") if is_contested(s))
    sensitivity = evaluate_hypotheses(
        records, args.baseline, args.focus, resamples=args.resamples, exclude=contested
    )
    for name, model in [
        ("metrics", metrics),
        ("summary", summary),
        ("replay", replay),
        ("audit_findings", audit),
    ]:
        write_json(Path(f"results/{name}.json"), model)
    payload = {
        "principal": as_dicts(hypotheses),
        "sensibilidade": as_dicts(sensitivity),
        "excluidos_na_sensibilidade": sorted(contested),
    }
    Path("results/hipoteses.json").write_bytes(
        (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    print(f"{len(records)} conversas, {len(models)} modelos, {len(metrics.rows)} linhas de métricas")
    for label, results in (("principal", hypotheses), ("sensibilidade", sensitivity)):
        for h in results:
            print(
                f"[{label}] {h.id}: diferença {h.difference:+.3f} (IC {h.ci95[0]:+.3f} a {h.ci95[1]:+.3f}), "
                f"p={h.p_value:.4f} -> {h.conclusion}"
            )


def cmd_generation_report(args: argparse.Namespace) -> None:
    """Analisa as conversas cruas da geração: acertos do professor e composição do dado de treino."""
    from labia.generation_report import summarize_generation
    from labia.runner import load_records

    records = load_records(*map(Path, args.runs))
    scenarios = {s.id: s for s in generate("train")}
    report = summarize_generation(records, scenarios)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    teacher = report["professor_primeira_tentativa"]
    print(
        f"{report['conversas']} conversas, {report['aprovadas']} aprovadas; professor: fraude "
        f"{teacher['fraude_que_passou']}, atrito {teacher['atrito']} -> {out}"
    )


def cmd_report(_: argparse.Namespace) -> None:
    """Reescreve a seção de resultados do README a partir de results/*.json."""
    from labia.contracts.metrics import MetricsFile
    from labia.report import HypothesisResult, inject, render_results

    metrics = MetricsFile.model_validate_json(Path("results/metrics.json").read_text(encoding="utf-8"))
    if metrics.is_sample:
        raise SystemExit("results/metrics.json é de exemplo: o README só recebe resultado real")
    hyp_path = Path("results/hipoteses.json")
    raw = json.loads(hyp_path.read_text(encoding="utf-8")) if hyp_path.exists() else {}

    def parse(items: list[dict[str, Any]]) -> list[HypothesisResult]:
        return [HypothesisResult(**{**h, "ci95": tuple(h["ci95"])}) for h in items]

    section = render_results(
        metrics,
        parse(raw.get("principal", [])),
        parse(raw.get("sensibilidade", [])),
        len(raw.get("excluidos_na_sensibilidade", [])),
    )
    readme = Path("README.md")
    readme.write_bytes(inject(readme.read_text(encoding="utf-8"), section).encode("utf-8"))
    print("README atualizado a partir de results/metrics.json e results/hipoteses.json")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="labia", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("schemas", help="gera os JSON Schemas do contrato de dados").set_defaults(func=cmd_schemas)

    p = sub.add_parser("scenarios", help="gera os cenários de treino e de teste")
    p.add_argument("--seed", type=int, default=20261110)
    p.add_argument("--train-per-cell", type=int, default=Counts.train_per_cell)
    p.add_argument("--test-per-cell", type=int, default=Counts.test_per_cell)
    p.add_argument("--test-heldout-per-cell", type=int, default=Counts.test_heldout_per_cell)
    p.set_defaults(func=cmd_scenarios)

    p = sub.add_parser("run", help="roda conversas com modelos de verdade")
    p.add_argument("--scenarios", required=True)
    p.add_argument("--ids", help="arquivo com os ids dos cenários a rodar, um por linha")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--model-id", required=True)
    p.add_argument("--defense", choices=[d.value for d in Defense], default="standard")
    p.add_argument("--agent-url", required=True)
    p.add_argument("--agent-model", required=True)
    p.add_argument("--agent-key-env", default="AGENT_API_KEY")
    p.add_argument("--sim-url", required=True)
    p.add_argument("--sim-model", required=True)
    p.add_argument("--sim-key-env", default="SIM_API_KEY")
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--max-turns", type=int, default=8)
    p.add_argument(
        "--max-calls", type=int, default=None, help="teto de chamadas novas por cliente nesta rodada"
    )
    p.add_argument("--cache-dir", default=".cache/llm")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("filter", help="filtro duplo e exportação do dataset de SFT")
    p.add_argument("runs", nargs="+")
    p.add_argument("--scenarios", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_filter)

    sub.add_parser("publish-check", help="recusa publicar dado de exemplo").set_defaults(
        func=cmd_publish_check
    )

    p = sub.add_parser("evaluate", help="gera os results/*.json reais a partir das conversas da avaliação")
    p.add_argument("runs", nargs="+")
    p.add_argument("--models", default="configs/modelos.json")
    p.add_argument("--release", default="v0")
    p.add_argument("--focus", default="sft")
    p.add_argument("--baseline", default="base")
    p.add_argument(
        "--fixed-threshold",
        type=float,
        default=0.05,
        help="fraude máxima para um achado contar como corrigido",
    )
    p.add_argument("--resamples", type=int, default=10_000)
    p.set_defaults(func=cmd_evaluate)

    sub.add_parser("report", help="reescreve os resultados do README").set_defaults(func=cmd_report)

    p = sub.add_parser("generation-report", help="analisa as conversas cruas da geração")
    p.add_argument("runs", nargs="+")
    p.add_argument("--out", default="experiments/04-geracao/analise.json")
    p.set_defaults(func=cmd_generation_report)

    p = sub.add_parser("samples", help="gera os arquivos de resultado de exemplo (is_sample: true)")
    p.add_argument("--resamples", type=int, default=2000)
    p.set_defaults(func=cmd_samples)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
