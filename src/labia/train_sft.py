"""Treino SFT do aluno com LoRA. Roda no Kaggle (GPU); localmente, só a parte sem GPU é testada.

Uso: python -m labia.train_sft --data sft.jsonl --out adaptador/ [--mode qlora|lora16] [--unsloth]
Para as duas GPUs: torchrun --nproc_per_node 2 -m labia.train_sft ...

Decisões que importam na T4 (medidas nos testes de fumaça):
- float16, porque a T4 não tem bfloat16;
- conversas acima de --max-len são descartadas e contadas, nunca cortadas no meio;
- o treino para sozinho ao bater no orçamento de tempo e salva o que aprendeu até ali.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from pathlib import Path
from typing import Any

from labia.training import IGNORE, Example, tokenize_for_sft

TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


def load_examples(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def encode_all(
    tokenizer: Any, rows: list[dict[str, Any]], max_len: int
) -> tuple[list[Example], dict[str, Any]]:
    encoded, dropped = [], 0
    for r in rows:
        ex = tokenize_for_sft(tokenizer, r["messages"], r.get("tools"), max_len=max_len)
        if ex is None:
            dropped += 1
        else:
            encoded.append(ex)
    lengths = sorted(len(e.input_ids) for e in encoded)
    stats = {
        "exemplos": len(encoded),
        "descartados_por_tamanho": dropped,
        "tokens_total": sum(lengths),
        "tokens_alvo": sum(e.n_target for e in encoded),
        "tokens_mediana": lengths[len(lengths) // 2] if lengths else 0,
        "tokens_max": lengths[-1] if lengths else 0,
    }
    return encoded, stats


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - precisa de GPU
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--model", default="Qwen/Qwen3-4B-Instruct-2507")
    p.add_argument("--mode", choices=["qlora", "lora16"], default="lora16")
    p.add_argument("--unsloth", action="store_true")
    p.add_argument("--max-len", type=int, default=6144)
    p.add_argument("--epochs", type=float, default=2.0)
    p.add_argument("--max-steps", type=int, default=-1)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--rank", type=int, default=16)
    p.add_argument("--grad-accum", type=int, default=8)
    p.add_argument("--time-budget-h", type=float, default=9.0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--limit", type=int, default=0, help="usa só os primeiros N exemplos (testes)")
    args = p.parse_args(argv)

    import torch
    from transformers import Trainer, TrainerCallback, TrainingArguments

    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    world = int(os.environ.get("WORLD_SIZE", "1"))
    is_main = local_rank == 0
    start = time.perf_counter()

    if args.unsloth:
        from unsloth import FastLanguageModel

        model, tokenizer = FastLanguageModel.from_pretrained(
            args.model, max_seq_length=args.max_len, load_in_4bit=args.mode == "qlora", dtype=torch.float16
        )
        model = FastLanguageModel.get_peft_model(
            model,
            r=args.rank,
            lora_alpha=2 * args.rank,
            lora_dropout=0.0,
            bias="none",
            target_modules=TARGET_MODULES,
            use_gradient_checkpointing="unsloth",
            random_state=args.seed,
        )
    else:
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        tokenizer = AutoTokenizer.from_pretrained(args.model)
        quant = None
        if args.mode == "qlora":
            quant = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
        model = AutoModelForCausalLM.from_pretrained(
            args.model, quantization_config=quant, dtype=torch.float16, device_map={"": local_rank}
        )
        if quant is not None:
            model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
        else:
            model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
            model.enable_input_require_grads()
        model = get_peft_model(
            model,
            LoraConfig(
                r=args.rank,
                lora_alpha=2 * args.rank,
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM",
                target_modules=TARGET_MODULES,
            ),
        )
        # LoRA em float32: treinar adaptadores em float16 puro estoura com facilidade (a T4 não tem bfloat16)
        for param in model.parameters():
            if param.requires_grad:
                param.data = param.data.float()
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    rows = load_examples(Path(args.data))
    random.Random(args.seed).shuffle(rows)
    if args.limit:
        rows = rows[: args.limit]
    encoded, data_stats = encode_all(tokenizer, rows, args.max_len)
    if is_main:
        print(json.dumps(data_stats, ensure_ascii=False), flush=True)

    class Data(torch.utils.data.Dataset):  # type: ignore[misc]
        def __len__(self) -> int:
            return len(encoded)

        def __getitem__(self, i: int) -> dict[str, list[int]]:
            e = encoded[i]
            return {"input_ids": e.input_ids, "attention_mask": e.attention_mask, "labels": e.labels}

    def collate(batch: list[dict[str, list[int]]]) -> dict[str, Any]:
        width = max(len(b["input_ids"]) for b in batch)

        def fill(key: str, value: int) -> Any:
            return torch.tensor([b[key] + [value] * (width - len(b[key])) for b in batch])

        return {
            "input_ids": fill("input_ids", tokenizer.pad_token_id),
            "attention_mask": fill("attention_mask", 0),
            "labels": fill("labels", IGNORE),
        }

    budget_s = args.time_budget_h * 3600

    class TimeBudget(TrainerCallback):  # type: ignore[misc]
        """Para o treino ao bater no orçamento de tempo; o adaptador até ali é salvo normalmente."""

        def on_step_end(self, a: Any, state: Any, control: Any, **kw: Any) -> Any:
            if time.perf_counter() - start > budget_s:
                control.should_training_stop = True
            return control

    training_args = TrainingArguments(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=max(1, args.grad_accum // world),
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        logging_steps=5,
        fp16=True,
        gradient_checkpointing=not args.unsloth and args.mode == "lora16",
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="adamw_torch",
        report_to="none",
        save_strategy="no",
        remove_unused_columns=False,
        seed=args.seed,
        ddp_find_unused_parameters=False,
        dataloader_num_workers=0,
    )
    trainer = Trainer(
        model=model, args=training_args, train_dataset=Data(), data_collator=collate, callbacks=[TimeBudget()]
    )
    torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    result = trainer.train()
    seconds = time.perf_counter() - t0
    steps = trainer.state.global_step
    seqs = steps * training_args.gradient_accumulation_steps * world
    mean_len = data_stats["tokens_total"] / max(1, data_stats["exemplos"])
    if is_main:
        trainer.save_model(args.out)
        tokenizer.save_pretrained(args.out)
        stats = {
            "modo": args.mode,
            "unsloth": args.unsloth,
            "gpus": world,
            "passos": steps,
            "segundos_treino": round(seconds, 1),
            "tokens_por_segundo": round(seqs * mean_len / seconds, 1),
            "pico_memoria_gb": round(torch.cuda.max_memory_allocated() / 1024**3, 2),
            "loss_media": round(result.training_loss, 4),
            "parou_por_tempo": time.perf_counter() - start > budget_s,
            "dados": data_stats,
            "log": [h for h in trainer.state.log_history if "loss" in h],
            "args": vars(args),
        }
        Path(args.out, "treino.json").write_text(
            json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps({k: v for k, v in stats.items() if k != "log"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":  # pragma: no cover
    main()
