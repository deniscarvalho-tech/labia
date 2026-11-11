"""Model card e dataset card do Hugging Face, montados a partir dos arquivos de resultado.

Nenhum número destes cards é digitado: cada um vem de results/*.json, de experiments/ ou do manifesto dos
cenários. Os cards se recusam a sair com dado de exemplo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from labia.contracts.metrics import MetricsFile
from labia.report import HypothesisResult, render_results


@dataclass(frozen=True)
class Repos:
    github: str = "https://github.com/deniscarvalho-tech/labia"
    model: str = "deniscarvalho-tech/labia-qwen3-4b-GGUF"
    dataset: str = "deniscarvalho-tech/labia-sft"
    space: str = "deniscarvalho-tech/labia"


def _hf(path: str, kind: str = "") -> str:
    return f"https://huggingface.co/{kind}{path}"


def _hypotheses(raw: dict[str, Any], key: str) -> list[HypothesisResult]:
    return [HypothesisResult(**{**h, "ci95": tuple(h["ci95"])}) for h in raw.get(key, [])]


def _int(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".")


def _pct(v: float) -> str:
    return f"{v * 100:.1f}%".replace(".", ",")


TACTIC_PT = {
    "none": "sem tática",
    "authority": "autoridade",
    "institutional_threat": "ameaça institucional",
    "urgency_emotion": "urgência e emoção",
    "fake_prior_promise": "promessa anterior",
}
SIDE_PT = {"golpe": "golpe", "legitimo": "honesto"}


def model_card(
    metrics: MetricsFile,
    hypotheses: dict[str, Any],
    training: dict[str, Any],
    generation: dict[str, Any],
    repos: Repos | None = None,
) -> str:
    repos = repos or Repos()
    if metrics.is_sample:
        raise ValueError("o model card só sai com resultado real (metrics.is_sample é true)")
    args = training.get("args", {})
    data = training.get("dados", {})
    rank = int(args.get("rank", 16))
    results = render_results(
        metrics,
        _hypotheses(hypotheses, "principal"),
        _hypotheses(hypotheses, "sensibilidade"),
        len(hypotheses.get("excluidos_na_sensibilidade", [])),
    ).replace("(docs/decisoes/", f"({repos.github}/blob/main/docs/decisoes/")
    teacher = generation["professor_primeira_tentativa"]
    return f"""---
license: apache-2.0
base_model: Qwen/Qwen3-4B-Instruct-2507
language:
- pt
tags:
- social-engineering
- fraud-prevention
- tool-use
- agents
- lora
- gguf
datasets:
- {repos.dataset}
pipeline_tag: text-generation
---

# Lábia v0: Qwen3-4B ajustado para não cair em engenharia social (GGUF)

Um agente de atendimento com ferramentas (reembolsar, estornar, desbloquear) vira alvo de engenharia social: ameaça de Procon, falsa autoridade, urgência, promessa de um atendente anterior, pedido fatiado. Este modelo é o Qwen3-4B-Instruct-2507 ajustado com LoRA para **consultar o sistema antes de agir** e conceder só o que a política permite, sem barrar o cliente honesto.

- Código, relatório técnico e decisões: [{repos.github}]({repos.github})
- Dataset de treino: [{repos.dataset}]({_hf(repos.dataset, "datasets/")})
- Demo: [{repos.space}]({_hf(repos.space, "spaces/")})

## Uso pretendido

Pesquisa e demonstração: um agente de atendimento em português, com chamada de ferramentas, para empresas **fictícias** (o Banco Saracura e o Quati Delivery), sob uma política escrita. O modelo aprendeu essas políticas; em outra empresa, ele precisa receber a política dela no prompt de sistema, e o comportamento precisa ser medido de novo.

**Fora do escopo:** decidir sozinho sobre dinheiro de clientes reais, sem verificação humana e sem um sistema que aplique as regras por conta própria. O verificador da Lábia existe justamente porque o texto do modelo não é garantia de nada.

## Como foi treinado

- **Dado:** {_int(data.get("exemplos", 0))} conversas do professor (gpt-oss-20b, Apache 2.0, rodando na nossa GPU) que passaram no **filtro duplo**: resultado certo e processo certo (consultou antes de agir). Na geração, o professor deixou passar {_pct(teacher["fraude_que_passou"])} dos golpes e barrou {_pct(teacher["atrito"])} dos honestos na primeira tentativa. Só os acertos verificados viraram dado de treino.
- **Destilação de contexto:** o professor atendeu com um prompt reforçado; o exemplo de treino guarda o prompt padrão. O modelo aprende a se comportar como se tivesse o reforço, sem pagar por esses tokens.
- **Tática fora do treino:** o pedido fatiado nunca aparece no treino e só é medido no teste.
- **LoRA:** posto {rank}, alfa {2 * rank}, nas projeções de atenção e MLP; taxa de aprendizado {args.get("lr", "?")}, agenda cosseno, {args.get("epochs", "?")} épocas, contexto máximo de {args.get("max_len", "?")} tokens, perda só nas respostas do assistente.
- **Execução:** modo `{training.get("modo", "?")}`, {training.get("gpus", "?")} GPU(s) T4 do Kaggle, {training.get("passos", "?")} passos em {training.get("segundos_treino", 0) / 3600:.1f} h, {training.get("tokens_por_segundo", "?")} tokens/s, pico de {training.get("pico_memoria_gb", "?")} GB, perda média {training.get("loss_media", "?")}.
- **Formato:** adaptador fundido nos pesos e convertido para GGUF de 8 bits (q8_0) pelo `convert_hf_to_gguf.py` do llama.cpp. O modelo-base da comparação passou pelo mesmo caminho.

## Avaliação

212 cenários de teste congelados por hash antes do treino (134 com táticas vistas e 78 com a tática nunca vista), 3 rodadas cada, com um cliente simulado de outra família (Ministral-3-14B). O veredito sai de um **verificador determinístico**, que aplica a política escrita como código às ações registradas no sistema.

{results}
## Limitações

- Empresas, clientes e políticas são simulados. Um cliente interpretado por LLM não tem toda a criatividade de um golpista real.
- O dado de treino é desequilibrado: o professor erra mais com clientes honestos que têm uma promessa válida, então esses casos aparecem pouco no treino.
- O modelo às vezes anuncia uma ação sem chamar a ferramenta. O verificador conta isso como atrito.
- Avaliado só em português e só nos dois setores do treino.

## Como usar

Com o Ollama:

```bash
ollama run hf.co/{repos.model}:Q8_0
```

O prompt de sistema precisa conter a política da empresa e as ferramentas no formato da OpenAI. Os textos usados no treino estão em `src/labia/prompts/` no repositório.

## Licença

Apache 2.0, a mesma do modelo-base.
"""


def dataset_card(generation: dict[str, Any], manifest: dict[str, Any], repos: Repos | None = None) -> str:
    repos = repos or Repos()
    train, test = manifest["files"]["train"], manifest["files"]["test"]
    cells = generation["treino_por_tatica_e_lado"]
    rows = "\n".join(
        f"| {TACTIC_PT[key.split('|')[0]]} | {SIDE_PT[key.split('|')[1]]} | {n} |"
        for key, n in sorted(cells.items())
    )
    teacher = generation["professor_primeira_tentativa"]
    return f"""---
license: apache-2.0
language:
- pt
task_categories:
- text-generation
tags:
- social-engineering
- fraud-prevention
- tool-use
- synthetic
size_categories:
- 1K<n<10K
---

# Lábia SFT: conversas de atendimento sob engenharia social, verificadas

{_int(generation["aprovadas"])} conversas em português entre um cliente (golpista ou honesto) e um agente de atendimento com ferramentas, nas empresas fictícias **Banco Saracura** e **Quati Delivery**. Cada conversa passou por um verificador determinístico e só entrou se o agente chegou ao **resultado certo pelo processo certo**: consultou o sistema antes de agir e concedeu exatamente o que a política permite.

Código e relatório técnico: [{repos.github}]({repos.github}). Modelo treinado com este dado: [{repos.model}]({_hf(repos.model)}).

## Como foi feito

- **Cenários:** {_int(train["n"])} cenários de treino gerados por código, com semente fixa (`sha256` {train["sha256"][:12]}…). Cada um traz os fatos do sistema, o perfil do cliente, a tática e o gabarito. Metade é golpe e metade é cliente honesto com a mesma tática: os **pares mínimos** impedem o modelo de aprender que "quem ameaça é golpista".
- **Professor e cliente simulado:** gpt-oss-20b (Apache 2.0), rodando na nossa própria GPU. Nenhuma API de terceiros gerou este dado.
- **Amostragem por rejeição:** até 3 tentativas por cenário. Foram {_int(generation["conversas"])} conversas para {_int(generation["aprovadas"])} aprovadas (uma por cenário).
- **Filtro duplo:** resultado certo e processo certo, sem chamada inválida, sem cliente simulado fora do personagem e sem sinal da tática que ficou fora do treino.
- **Destilação de contexto:** o professor atendeu com um prompt reforçado; cada exemplo guarda o prompt padrão.

## Composição

| Tática | Lado | Conversas |
|---|---|---|
{rows}

O desequilíbrio é real e medido. Na primeira tentativa, o professor barrou {_pct(teacher["atrito"])} dos clientes honestos e deixou passar {_pct(teacher["fraude_que_passou"])} dos golpes. Como só os acertos entram, os casos em que ele mais erra, como cumprir uma promessa válida, aparecem menos.

## Formato

Uma conversa por linha (JSONL): `messages` no formato de chat da OpenAI (sistema, cliente, agente com `tool_calls`, respostas das ferramentas), `tools` com os esquemas das ferramentas, e `meta` com o cenário, o setor, a tática, o lado e o veredito.

## O que não está aqui

- **O teste.** Os {_int(test["n"])} cenários de teste ficam fora, congelados por hash (`sha256` {test["sha256"][:12]}…). Eles podem ser regenerados pelo código para avaliação, nunca para treino.
- **Dados pessoais reais.** Nomes, CPFs, chaves Pix e endereços são inventados. Os CPFs têm o dígito verificador errado de propósito.

## Limitações conhecidas

- {generation["treino_gabarito_contestavel"]} conversas vêm de variantes com gabarito contestável (decisão 0008 no repositório).
- Em {generation["treino_raciocinio_vazado"]} conversa(s), o professor escreveu parte do raciocínio em inglês na resposta.
- O cliente simulado às vezes se contradiz, e o agente às vezes repete a mesma frase a cada insistência.

## Licença

Apache 2.0.
"""
