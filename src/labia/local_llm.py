"""O modelo em GGUF rodando na CPU com llama.cpp: o agente da demo ao vivo e do teste de latência na CPU.

O prompt é montado pelo template de chat do próprio Qwen (o mesmo do treino), e as chamadas de ferramenta
saem do texto (`<tool_call>{...}</tool_call>`), com o mesmo leitor que o benchmark usa como plano B.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from labia.llm import ChatRequest, ChatResponse, extract_text_tool_calls

STOP = ["<|im_end|>", "<|endoftext|>"]


class LlamaCppClient:
    def __init__(
        self, gguf_path: str, tokenizer_repo: str, *, n_ctx: int = 8192, n_threads: int | None = None
    ) -> None:
        from llama_cpp import Llama
        from transformers import AutoTokenizer

        self.llm = Llama(model_path=gguf_path, n_ctx=n_ctx, n_threads=n_threads, verbose=False)
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_repo)
        # O llama.cpp não é seguro entre threads; a demo atende uma pessoa por vez.
        self.lock = threading.Lock()
        self.states: dict[str, Any] = {}

    def render(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None, *, generation: bool = True
    ) -> str:
        prompt = self.tokenizer.apply_chat_template(
            messages, tools=tools, add_generation_prompt=generation, tokenize=False
        )
        return str(prompt)

    def warm(self, key: str, system: dict[str, Any], tools: list[dict[str, Any]] | None) -> None:
        """Lê uma vez o começo fixo de um cenário (política e ferramentas) e guarda o estado do modelo.

        Na CPU, ler esses cerca de 2.500 tokens leva uns 3 minutos. Com o estado guardado, a primeira resposta
        ao cliente só lê o que vem depois, porque o llama.cpp reaproveita o prefixo comum.
        """
        prefix = self.render([system], tools, generation=False)
        with self.lock:
            self.llm.reset()
            self.llm.eval(self.llm.tokenize(prefix.encode("utf-8"), special=True))
            self.states[key] = self.llm.save_state()

    def restore(self, key: str) -> bool:
        """Volta o modelo ao estado guardado do cenário. Devolve se havia estado."""
        state = self.states.get(key)
        if state is None:
            return False
        with self.lock:
            self.llm.load_state(state)
        return True

    def complete(self, request: ChatRequest) -> ChatResponse:
        prompt = self.render(request.messages, request.tools)
        with self.lock:
            start = time.perf_counter()
            out = self.llm.create_completion(
                prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                seed=request.seed if request.seed is not None else -1,
                stop=STOP,
            )
            latency = time.perf_counter() - start
        text = out["choices"][0]["text"]
        content, calls = extract_text_tool_calls(text)
        usage = out.get("usage", {})
        return ChatResponse(
            content=content,
            tool_calls=calls,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            latency_s=latency,
            finish_reason=out["choices"][0].get("finish_reason"),
        )
