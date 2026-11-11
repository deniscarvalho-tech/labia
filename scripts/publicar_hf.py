"""Publica a Lábia no Hugging Face: o modelo (GGUF e model card), o dataset (SFT e dataset card) e a demo.

A chave vem da variável de ambiente HF_TOKEN, nunca do repositório. Sem `--publicar`, o script só mostra o
que faria. Antes de publicar, ele roda `labia publish-check` (recusa dado de exemplo) e `labia cards`.

    uv run python scripts/publicar_hf.py --gguf data/modelos/labia-sft-q8_0.gguf            # ensaio
    uv run python scripts/publicar_hf.py --gguf data/modelos/labia-sft-q8_0.gguf --publicar # de verdade
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gguf", required=True, help="o GGUF do modelo ajustado")
    p.add_argument("--sft", default="data/sft/train.jsonl", help="o dado de treino (as duas fatias juntas)")
    p.add_argument("--usuario", default="deniscarvalho-tech", help="a conta ou organização no Hugging Face")
    p.add_argument("--publicar", action="store_true", help="sem esta opção, só mostra o que faria")
    args = p.parse_args()

    gguf, sft = Path(args.gguf), Path(args.sft)
    for f in (gguf, sft, ROOT / "results" / "replay.json"):
        if not f.exists():
            sys.exit(f"não encontrei {f}")
    run(["labia", "publish-check"])
    run(["labia", "cards", "--out", "hf"])
    model_repo = f"{args.usuario}/labia-qwen3-4b-GGUF"
    dataset_repo = f"{args.usuario}/labia-sft"
    space_repo = f"{args.usuario}/labia"
    plan = [
        ("modelo", model_repo, [(gguf, gguf.name), (ROOT / "hf" / "model-card.md", "README.md")]),
        (
            "dataset",
            dataset_repo,
            [(sft, "data/train.jsonl"), (ROOT / "hf" / "dataset-card.md", "README.md")],
        ),
        (
            "space",
            space_repo,
            [
                *[(f, f.name) for f in (ROOT / "space").glob("*") if f.is_file()],
                (ROOT / "results" / "replay.json", "data/replay.json"),
            ],
        ),
    ]
    for kind, repo, files in plan:
        print(f"\n{kind}: https://huggingface.co/{'' if kind == 'modelo' else kind + 's/'}{repo}")
        for src, dst in files:
            print(
                f"  {src.relative_to(ROOT) if src.is_relative_to(ROOT) else src} -> {dst} ({src.stat().st_size / 1e6:.1f} MB)"
            )
    if not args.publicar:
        print("\nensaio: nada foi enviado. Rode de novo com --publicar.")
        return

    token = os.environ.get("HF_TOKEN")
    if not token:
        sys.exit("defina HF_TOKEN no ambiente (no .env, nunca no repositório)")
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    for kind, repo, files in plan:
        repo_type = {"modelo": "model", "dataset": "dataset", "space": "space"}[kind]
        api.create_repo(
            repo, repo_type=repo_type, exist_ok=True, space_sdk="gradio" if kind == "space" else None
        )
        for src, dst in files:
            api.upload_file(path_or_fileobj=str(src), path_in_repo=dst, repo_id=repo, repo_type=repo_type)
        print(f"{kind}: publicado em {repo}")
    api.add_space_variable(space_repo, "LABIA_MODEL_REPO", model_repo)
    api.add_space_variable(space_repo, "LABIA_MODEL_FILE", gguf.name)


if __name__ == "__main__":
    main()
