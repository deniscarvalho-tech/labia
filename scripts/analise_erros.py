"""Números da análise de erros do README, a partir das conversas da avaliação.

    uv run python scripts/analise_erros.py data/avaliacao/base/avaliacao/base.jsonl data/avaliacao/sft/avaliacao/sft.jsonl

Grava experiments/07-avaliacao/analise-de-erros.json.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from labia.contracts.common import Split, Verdict
from labia.evaluate import split_of
from labia.generation_report import claimed_without_action
from labia.runner import load_records

OUT = Path("experiments/07-avaliacao/analise-de-erros.json")


def main(paths: list[str]) -> None:
    records = load_records(*map(Path, paths))
    report: dict[str, Any] = {}
    for model in sorted({r.model_id for r in records}):
        recs = [r for r in records if r.model_id == model]
        honest = [r for r in recs if r.legit]
        denied = [r for r in honest if r.verdict == Verdict.FRICTION_DENIED]
        fraud = [r for r in recs if not r.legit and r.verdict == Verdict.FRAUD_PASSED]
        heldout_fraud = [r for r in fraud if split_of(r) == Split.HELDOUT_TACTIC]
        report[model] = {
            "honestos": len(honest),
            "honestos_negados": len(denied),
            "negados_anunciando_acao_sem_executar": sum(claimed_without_action(r) for r in denied),
            "conversas_encerradas_por_transferencia": sum(r.ended_by == "escalated" for r in recs),
            "conversas": len(recs),
            "fraudes_que_passaram": len(fraud),
            "fraudes_no_pedido_fatiado_por_situacao": dict(
                Counter(r.situation for r in heldout_fraud).most_common()
            ),
            "regras_violadas_nas_fraudes": dict(
                Counter(v for r in fraud for v in r.violated_rules).most_common()
            ),
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
