"""Linha de comando da Lábia: `labia <comando>`. O Makefile chama estes comandos."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from labia.contracts import export_schemas
from labia.scenarios.generator import Counts, dump_jsonl, generate

DATA = Path("data")


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

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
