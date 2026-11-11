# ADR 0007: o professor é o gpt-oss-20b

- **Status:** aceita em 11/11/2026, pendente só da revisão humana do português (critério da regra)
- **Data:** 11/11/2026

## Contexto

A ADR 0003 deixou dois candidatos a professor, ambos Apache 2.0 e rodando na nossa GPU: o Qwen3-30B-A3B-Instruct-2507 e o gpt-oss-20b. A regra de decisão foi escrita antes do piloto: **vence quem produzir mais conversas aprovadas por hora de GPU, com pelo menos 95% de chamadas de ferramenta válidas e português aprovado numa revisão humana de 10 conversas.**

## O que o piloto mediu

Mesmos 28 cenários de treino (um golpe e um legítimo de cada uma das 14 situações), cada candidato fazendo os dois papéis (atendente com o prompt reforçado e cliente simulado), 8 conversas em paralelo. Fonte: `experiments/01-piloto-professor-v2/resumo.json`.

| Candidato | Aprovadas por hora | Aprovação | Chamadas válidas | Clientes honestos barrados |
|---|---|---|---|---|
| **gpt-oss-20b** | **273,9** | **75%** | 100% | 3 de 14 |
| Qwen3-30B-A3B | 242,8 | 54% | 100% | 7 de 14 |

A primeira versão do piloto (`experiments/01-piloto-professor-v1`) foi descartada: o Qwen, como cliente simulado, terminava a primeira mensagem com `[FIM]`, e o laço encerrava a conversa antes de o agente responder. O defeito era do laço (aceitar o fim antes da primeira resposta) e foi corrigido em `5e58662`.

## Decisão

O professor e o simulador do treino são o **gpt-oss-20b**, com raciocínio no nível baixo (`reasoning_effort: low`), servido pelo Ollama.

## Ressalvas honestas

- Com 28 conversas, a diferença em aprovadas por hora (274 contra 243) é pequena perto da incerteza. A diferença na taxa de aprovação (75% contra 54%) é maior e aponta para o mesmo lado, e a regra foi seguida como escrita.
- A revisão do português (`docs/revisao/revisao-portugues-professor.md`) ainda não foi feita. Se reprovar, a decisão volta para o Qwen, que é o segundo colocado.
- Qualidades vistas na leitura: o cliente simulado às vezes se contradiz (mistura a verdade da situação com a mentira) e o atendente repete a mesma frase a cada insistência. Nenhuma das duas muda o veredito; ficam registradas como limitação do dado de treino.

## Consequências

- O simulador da avaliação (Ministral-3-14B) continua de outra família, como manda a decisão 6 do plano.
- Na avaliação, agente e simulador ficam em servidores separados, um por GPU: o piloto mostrou que dois modelos grandes no mesmo servidor ficam se revezando na GPU e derrubam a vazão.
