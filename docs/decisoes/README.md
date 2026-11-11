# Registro de decisões (ADR)

**ADR** quer dizer *Architecture Decision Record*: um arquivo curto para cada decisão importante do projeto. A prática foi popularizada por Michael Nygard em 2011. A ideia é simples: daqui a seis meses (ou numa entrevista), ninguém lembra por que escolheu X em vez de Y. O ADR responde.

Todo ADR tem o mesmo formato:

1. **Contexto:** o problema e as restrições.
2. **Opções consideradas:** inclusive as que foram descartadas, com o motivo.
3. **Decisão:** o que escolhemos.
4. **Consequências:** o que ganhamos e o que perdemos. Toda decisão tem custo.
5. **Como vamos validar:** o teste que mostra se a decisão estava certa.
6. **Referências.**

**Status possíveis:** `proposta` (aguardando o seu ok) → `aceita` → `substituída por ADR-XXXX`, quando mudamos de ideia. Um ADR aceito nunca é apagado: se a decisão mudar, escrevemos um novo que substitui o antigo. O histórico de raciocínio também é informação.

## Índice

| # | Decisão | Status |
|---|---|---|
| [0001](0001-verificador-deterministico.md) | O verificador determinístico é o juiz principal | aceita |
| [0002](0002-modelo-base.md) | Modelo base: Qwen3-4B-Instruct-2507 | aceita |
| [0003](0003-professor-e-simuladores.md) | Professor e simuladores na nossa GPU (custo zero); APIs gratuitas só para avaliação; destilação de contexto | aceita (revisão 2) |
| [0004](0004-divisao-anti-vazamento.md) | Divisão por cenário e fracionamento como tática fora do treino | aceita |
| [0005](0005-metricas-e-estatistica.md) | Métricas, intervalos de confiança e critérios de decisão | aceita |
| [0006](0006-ollama-e-estado-em-memoria.md) | Ollama no lugar do llama.cpp compilado, e estado da sandbox em memória | aceita |
| [0007](0007-professor-gpt-oss.md) | O professor é o gpt-oss-20b | aceita (falta a revisão do português) |

ADRs previstos para os próximos dias: LoRA × QLoRA e hiperparâmetros (sexta, no treino), formato e quantização do GGUF (sábado) e estratégia do DPO (v1.1).
