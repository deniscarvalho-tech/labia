"""Roda lotes de conversas em paralelo e grava cada uma numa linha de JSONL assim que termina.

Gravar linha a linha importa no Kaggle: se a sessão cair no meio, o que já rodou não se perde, e o cache
de respostas faz a retomada não chamar o modelo de novo.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from labia.agents import Agent, Customer
from labia.contracts.common import Defense
from labia.conversation import ConversationRecord, run_conversation
from labia.scenarios.model import Scenario


def run_seed(scenario: Scenario, run: int, role: str) -> int:
    """Semente estável por cenário, rodada e papel: as 3 rodadas diferem, e repetir dá o mesmo."""
    digest = hashlib.sha256(f"{scenario.id}|{run}|{role}".encode()).hexdigest()
    return int(digest[:8], 16)


@dataclass(frozen=True)
class Job:
    scenario: Scenario
    run: int


def done_keys(path: Path) -> set[tuple[str, int]]:
    if not path.exists():
        return set()
    keys = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            keys.add((rec["scenario_id"], rec["run"]))
    return keys


def run_batch(
    jobs: list[Job],
    make_agent: Callable[[Scenario, int], Agent],
    make_customer: Callable[[Scenario, int], Customer],
    out: Path,
    *,
    model_id: str,
    defense: Defense,
    workers: int = 4,
    max_turns: int = 8,
    log_every: int = 10,
) -> list[ConversationRecord]:
    """Roda os jobs que ainda não estão no arquivo de saída (retomável) e devolve os novos registros."""
    out.parent.mkdir(parents=True, exist_ok=True)
    already = done_keys(out)
    pending = [j for j in jobs if (j.scenario.id, j.run) not in already]
    lock = threading.Lock()
    records: list[ConversationRecord] = []
    start = time.perf_counter()

    def one(job: Job) -> ConversationRecord:
        return run_conversation(
            job.scenario,
            make_agent(job.scenario, job.run),
            make_customer(job.scenario, job.run),
            model_id=model_id,
            defense=defense,
            run=job.run,
            max_turns=max_turns,
        )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one, j) for j in pending]
        for i, fut in enumerate(as_completed(futures), start=1):
            rec = fut.result()
            with lock:
                with out.open("ab") as fh:
                    fh.write((rec.model_dump_json() + "\n").encode("utf-8"))
                records.append(rec)
            if i % log_every == 0 or i == len(pending):
                elapsed = time.perf_counter() - start
                print(
                    f"[{model_id}] {i}/{len(pending)} conversas em {elapsed / 60:.1f} min "
                    f"({i / max(elapsed, 1e-9) * 3600:.0f} por hora)",
                    flush=True,
                )
    return records


def load_records(*paths: Path) -> list[ConversationRecord]:
    records = []
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(ConversationRecord.model_validate_json(line))
    return records
