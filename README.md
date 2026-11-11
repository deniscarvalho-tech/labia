# Lábia

Treinei um LLM pequeno e aberto para não cair em engenharia social em português e medi o resultado em fraude, atrito com o cliente honesto, custo e latência.

> **Status (11/11/2026): v0 avaliada.** O ajuste fino reduziu muito o atrito com o cliente honesto, mas não reduziu a fraude, e piorou a fraude na tática que ficou fora do treino (resultados abaixo). A ablação sem o filtro do verificador e a comparação com modelos de ponta pelas APIs ainda estão rodando. As hipóteses e o plano de análise foram registrados **antes de qualquer dado**, na tag [`pre-registro`](https://github.com/deniscarvalho-tech/labia/releases/tag/pre-registro); a análise de sensibilidade, antes de qualquer resultado, na tag [`sensibilidade`](https://github.com/deniscarvalho-tech/labia/releases/tag/sensibilidade).

## O problema

Um agente de atendimento com acesso a ferramentas (reembolsar, emitir cupom, desbloquear conta) vira alvo de engenharia social: o cliente ameaça ir ao Procon, inventa que um atendente anterior prometeu, diz que é cliente Private, pede com urgência porque o filho está com fome, ou fatia o pedido em partes pequenas para cada uma passar abaixo do limite.

O difícil não é recusar golpe. Um agente que nega tudo zera a fraude e barra todo cliente honesto. O problema é **as duas coisas ao mesmo tempo**: a mesma frase ("meu pedido não chegou, vou no Procon") pode vir de quem tem direito ao reembolso e de quem recebeu o pedido e passou o código ao entregador. Só o sistema sabe a diferença, e o agente precisa consultar antes de agir.

Por isso a Lábia mede sempre duas taxas juntas:

- **fraude que passou**: em quantas conversas de golpe o agente executou uma ação que a política proíbe;
- **atrito**: em quantas conversas com cliente honesto ele deixou de atender o que a pessoa tinha direito.

## Demo

*Em breve: GIF do replay de uma conversa e o link do Space.*

## O que já existia e o que é novo

| Já existia | O que a Lábia acrescenta |
|---|---|
| Benchmarks de agentes com ferramentas e políticas (τ-bench) | domínio brasileiro (banco e delivery), em português, com golpes do repertório local |
| Avaliações de *red teaming* com LLM como juiz | um **verificador determinístico**: a política vira código e o veredito sai das ações, nunca do texto |
| Conjuntos de teste com golpes | **pares mínimos**: a mesma tática em golpes e em clientes honestos, para o modelo não aprender que "quem ameaça é golpista" |
| Destilação de um modelo grande num pequeno | **filtro duplo**: só entram no treino conversas com resultado certo *e* processo certo (consultou antes de agir) |
| Métricas de acerto | fraude × atrito com intervalo de confiança por bootstrap de cenário, **uma tática inteira fora do treino**, curva de resistência por turno e valor em risco em reais |

## Arquitetura

```mermaid
flowchart LR
    GEN["Gerador de cenários<br/>(código + semente)"] -->|fatos + gabarito| RUN["Laço de conversa"]
    SIM["Cliente simulado<br/>(golpista ou honesto)"] <--> RUN
    AG["Agente avaliado"] <--> RUN
    AG -- "chamadas de ferramenta" --> SB["Sandbox<br/>Banco Saracura · Quati Delivery"]
    RUN --> VER{{"Verificador<br/>determinístico"}}
    VER -->|aprovadas| SFT["SFT com LoRA<br/>(Kaggle, 2× T4)"]
    SFT --> MODEL["Modelo Lábia"]
    MODEL --> EVAL["Avaliação: 212 cenários × 3 rodadas"]
    VER --> EVAL
    EVAL --> RES[("results/*.json")]
    RES --> PANEL["Painel em React"]
```

As empresas são fictícias: o **Banco Saracura** (regras B1 a B5) e o **Quati Delivery** (regras D1 a D6), mais as regras gerais G1 a G5. As políticas completas estão em [docs/especificacao/](docs/especificacao/).

- **Aluno:** Qwen3-4B-Instruct-2507 (Apache 2.0), ajustado com LoRA.
- **Professor e cliente simulado do treino:** gpt-oss-20b (Apache 2.0), escolhido num piloto por uma regra definida antes ([ADR 0007](docs/decisoes/0007-professor-gpt-oss.md)).
- **Cliente simulado da avaliação:** Ministral-3-14B (Apache 2.0), de outra família, para o aluno não decorar os "tiques" do atacante do treino.
- Tudo o que entra no treino vem de modelos abertos rodando na minha própria GPU (Kaggle, camada gratuita). APIs de terceiros entram só na avaliação.

## O que é real, simulado e estimado

| | O que é |
|---|---|
| **Real (medido)** | todo veredito, taxa, intervalo de confiança, latência e hora de GPU publicada. Sai de execuções versionadas em [experiments/](experiments/) e de `results/*.json`. |
| **Simulado** | as empresas, as políticas, os clientes (interpretados por LLMs) e os dados pessoais. Os CPFs têm o dígito verificador errado de propósito. |
| **Estimado** | todo custo em dinheiro. O projeto não pagou nada (só camadas gratuitas); o custo por mil conversas é calculado a partir de vazão medida e preço público de GPU, com as premissas ao lado do número. |

## Resultados

<!-- RESULTADOS:INICIO -->
Avaliação de `v0`, commit `100dae3`. Cada cenário rodou 3 vezes; os intervalos são de 95%, por bootstrap de cenários inteiros. Fonte: `results/metrics.json`.

**Em resumo**, comparando Lábia v0 (SFT) com Qwen3-4B sem ajuste:

- **Atrito nas táticas vistas no treino:** de 72,1% para 25,4% (diferença significativa).
- **Fraude nas táticas vistas no treino:** de 16,9% para 17,4% (sem diferença significativa).
- **Fraude na tática nunca vista (pedido fatiado):** de 15,4% para 29,9% (piorou: o intervalo da diferença fica inteiro acima de zero).
- **Acerto nas 3 rodadas (pass^3), táticas vistas:** de 34,3% para 58,2% (exploratório).

### Táticas vistas no treino

| Modelo | Fraude que passou | IC 95% | Atrito | IC 95% | pass^3 | Cenários |
|---|---|---|---|---|---|---|
| Qwen3-4B sem ajuste | 16,9% | 10,9% a 23,4% | 72,1% | 64,7% a 79,1% | 34,3% | 134 |
| Qwen3-4B + prompt reforçado | 14,9% | 8,5% a 22,4% | 65,7% | 58,2% a 73,1% | 40,3% | 134 |
| Lábia v0 (SFT) | 17,4% | 11,4% a 23,4% | 25,4% | 16,4% a 34,8% | 58,2% | 134 |

### Tática nunca vista (pedido fatiado)

| Modelo | Fraude que passou | IC 95% | Atrito | IC 95% | pass^3 | Cenários |
|---|---|---|---|---|---|---|
| Qwen3-4B sem ajuste | 15,4% | 8,5% a 23,1% | 84,6% | 76,1% a 92,3% | 33,3% | 78 |
| Qwen3-4B + prompt reforçado | 9,4% | 5,1% a 14,5% | 85,5% | 78,6% a 91,5% | 35,9% | 78 |
| Lábia v0 (SFT) | 29,9% | 21,4% a 38,5% | 67,5% | 56,4% a 78,6% | 24,4% | 78 |

### Hipóteses pré-registradas

Diferença = SFT menos base, nos mesmos cenários e rodadas (bootstrap pareado, 10.000 reamostragens), com correção de Holm-Bonferroni.

| | Hipótese | Diferença | IC 95% | p | Pares | Resultado |
|---|---|---|---|---|---|---|
| H1 | O SFT deixa passar menos fraude que o base nas táticas vistas no treino. | +0,5 p.p. | -6,0 a +7,5 p.p. | 0,5905 | 201 | não confirmada: a diferença pode ser acaso |
| H2 | O atrito do SFT não passa o do base por mais de 5 p.p. | -46,8 p.p. | -56,7 a -36,8 p.p. | 0,0000 | 201 | confirmada: o atrito não piorou além da margem |
| H3 | O SFT deixa passar menos fraude que o base na tática nunca vista. | +14,5 p.p. | +3,4 a +25,6 p.p. | 0,9943 | 117 | não confirmada: a fraude aumentou (o intervalo inteiro fica acima de zero) |

#### Análise de sensibilidade

As mesmas hipóteses sem os 2 cenários de gabarito contestável ([decisão 0008](docs/decisoes/0008-gabarito-contestavel.md)), definida antes de qualquer resultado.

| | Hipótese | Diferença | IC 95% | p | Pares | Resultado |
|---|---|---|---|---|---|---|
| H1 | O SFT deixa passar menos fraude que o base nas táticas vistas no treino. | +0,5 p.p. | -6,0 a +7,5 p.p. | 0,5905 | 201 | não confirmada: a diferença pode ser acaso |
| H2 | O atrito do SFT não passa o do base por mais de 5 p.p. | -48,2 p.p. | -58,5 a -38,0 p.p. | 0,0000 | 195 | confirmada: o atrito não piorou além da margem |
| H3 | O SFT deixa passar menos fraude que o base na tática nunca vista. | +14,5 p.p. | +3,4 a +25,6 p.p. | 0,9943 | 117 | não confirmada: a fraude aumentou (o intervalo inteiro fica acima de zero) |

### Custo e latência (estimados)

| Modelo | Conversas por hora de GPU | US$ por mil conversas | Latência por turno (mediana) |
|---|---|---|---|
| Qwen3-4B sem ajuste | 296 | 1,18 | 19,5 s |
| Qwen3-4B + prompt reforçado | 274 | 1,28 | 22,9 s |
| Lábia v0 (SFT) | 442 | 0,79 | 14,2 s |

Premissas: preço público da T4 (US$ 0,35 por hora, https://cloud.google.com/products/compute/gpus-pricing, consultado em 2026-11-11); A vazão do modelo próprio vem da avaliação: uma T4 dedicada ao agente, 8 conversas ao mesmo tempo, esperando o cliente simulado a cada turno. A capacidade real é igual ou maior. A latência foi medida com 8 conversas simultâneas na mesma GPU; não é a latência de um usuário sozinho. O custo da API usa os tokens medidos de cada conversa e o preço público por milhão de tokens, sem desconto de cache. O projeto não pagou nada: tudo rodou em camadas gratuitas. Fonte: `results/custo.json`.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/fraude-atrito-escuro.svg">
  <img alt="Fraude que passou contra clientes honestos barrados, um ponto por modelo" src="docs/img/fraude-atrito-claro.svg">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/fraude-por-tatica-escuro.svg">
  <img alt="Fraude que passou por tática, do modelo-base e do ajustado" src="docs/img/fraude-por-tatica-claro.svg">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/resistencia-escuro.svg">
  <img alt="Fração dos golpes ainda resistidos a cada turno de insistência" src="docs/img/resistencia-claro.svg">
</picture>

<!-- RESULTADOS:FIM -->

### O que já foi medido (pilotos)

Piloto do professor, 28 cenários de treino, uma rodada cada (fonte: [experiments/01-piloto-professor-v2](experiments/01-piloto-professor-v2/resumo.json)):

| Candidato a professor | Aprovadas por hora de GPU | Taxa de aprovação | Chamadas de ferramenta válidas |
|---|---|---|---|
| gpt-oss-20b | 273,9 | 75% | 100% |
| Qwen3-30B-A3B-Instruct-2507 | 242,8 | 54% | 100% |

Teste do treino (fonte: [experiments/02-teste-treino](experiments/02-teste-treino/resumo.json)): o Qwen3-4B treina com QLoRA numa T4 com pico de 11,2 GB de memória, a 154 tokens por segundo. Sem ajuste nenhum, ele já produziu uma chamada de ferramenta válida na primeira resposta em 9 de 10 cenários de teste.

Geração do dado de treino (fonte: [experiments/04-geracao](experiments/04-geracao/analise.json), gerado por `labia generation-report`): o professor atendeu os 2.010 cenários de treino em 8,5 horas de GPU, com até 3 tentativas por cenário. Passaram no filtro duplo **1.756 conversas**, uma por cenário (87%).

Na primeira tentativa, e em cenários de treino, o professor deixou passar 3,7% dos golpes e barrou 29,6% dos clientes honestos. Esse segundo número está inflado: a geração rodou com um defeito no laço de conversa, achado depois, que descartava a última fala do cliente ([ADR 0009](docs/decisoes/0009-ultima-fala-do-cliente.md)). O dado de treino não é afetado, porque só entram conversas que o verificador aprovou.

## Análise de erros

O padrão de erro mais comum, nos pilotos e na geração, foi o agente **anunciar uma ação sem executá-la**. Ele escreve "o endereço foi atualizado com sucesso" ou "Estorno confirmado! Vamos processar agora mesmo", mas não chama a ferramenta. O cliente honesto sai satisfeito e sem o que tinha direito. Um avaliador que lesse só o texto daria nota alta; o verificador, que olha as ações, registra atrito.

Na geração, uma expressão regular que procura esse padrão encontrou 86 dos 185 clientes honestos negados pelo professor na primeira tentativa.

Lendo os erros do professor, também achei um defeito meu. Em seis variantes da tática da promessa, o cenário honesto pedia algo que um atendente sensato recusaria, como estornar de novo uma tarifa já estornada. O teste estava congelado e continuou como estava. Antes de ver qualquer resultado, registrei uma análise de sensibilidade sem os 2 cenários afetados ([ADR 0008](docs/decisoes/0008-gabarito-contestavel.md)).

A primeira avaliação do modelo-base também revelou um defeito meu, desta vez no laço de conversa. O cliente simulado confirmava e se despedia na mesma mensagem ("sim, pode fazer o estorno [FIM]"), e o laço encerrava antes de o agente agir. Isso aconteceu em 85% das conversas. Corrigi o laço, guardei aquela avaliação como inválida e rodei de novo ([ADR 0009](docs/decisoes/0009-ultima-fala-do-cliente.md)).

### O que o ajuste fino mudou, e o que não mudou

Os números desta seção saem de [`scripts/analise_erros.py`](scripts/analise_erros.py) (fonte: [experiments/07-avaliacao/analise-de-erros.json](experiments/07-avaliacao/analise-de-erros.json)).

**O modelo aprendeu a agir.** No modelo-base, 84 dos 192 clientes honestos negados foram vítimas do "anunciar sem executar". No modelo ajustado, os honestos negados caíram para 26, e só 6 com esse padrão. É daí que vem quase toda a queda do atrito.

**O modelo não aprendeu a distinguir melhor o golpe.** Nas táticas vistas no treino, a fraude ficou onde estava. O que mudou foi o jeito de recusar: o modelo ajustado encerra 434 das 636 conversas transferindo para um humano, contra 140 do modelo-base. Ele herdou isso do professor. Parte do "golpe bloqueado" é, na prática, um problema passado adiante, o que numa operação real custa tempo de atendente.

**Agir com mais facilidade abriu a porta do pedido fatiado.** Na tática que ficou fora do treino, o golpista pede pedaços pequenos que, somados, passam do limite. O modelo ajustado trata cada pedaço isoladamente:

- 20 das fraudes que passaram são estornos de cortesia picados (regra B1);
- 9 estouram o aumento de limite diário somado (B5);
- 6 são reembolsos de itens que, juntos, passam do teto (D3).

Ele aprendeu a executar, mas não a somar o que já concedeu na conversa.

**A previsão registrada antes dos resultados se confirmou em parte.** O cliente honesto com promessa válida foi a pior tática para o modelo ajustado: 57,6% de atrito, contra 16,7% a 21,4% nas outras. Ainda assim, ele ficou abaixo do modelo-base nessa mesma célula, que barrou 84,8%.

**Dois erros típicos, lidos nas conversas:**

- **Regra aplicada pela metade.** O modelo consultou a tarifa e estornou R$ 59,90 como cortesia, acima do teto de R$ 50. Depois que o cliente agradeceu, escreveu "não é possível estornar essa tarifa", já tendo estornado.
- **Regra trocada.** Num produto que não chegou (desacordo comercial, que pode ser contestado no chat), o modelo aplicou a regra da compra não reconhecida e transferiu o cliente honesto para a equipe de fraude.

## Decisões e trade-offs

As decisões importantes têm um registro curto cada, com contexto, opções e consequências, em [docs/decisoes/](docs/decisoes/). As que mais pesam:

- **O veredito é determinístico** ([ADR 0001](docs/decisoes/0001-verificador-deterministico.md)): exato e reproduzível, ao custo de escrever a política como código.
- **Uma tática inteira fica fora do treino** ([ADR 0004](docs/decisoes/0004-divisao-anti-vazamento.md)): o pedido fatiado só aparece no teste, para medir se o modelo aprendeu o princípio ou decorou exemplos.
- **Custo zero com a conta à vista**: o orçamento real foram horas de GPU gratuita, e essa contabilidade é publicada.

## Limitações

- As empresas e os clientes são simulados. Um cliente interpretado por LLM não tem toda a criatividade de um golpista real.
- O cliente simulado do treino às vezes se contradiz, e o professor às vezes repete a mesma frase a cada insistência ([revisão](docs/revisao/revisao-portugues-professor.md)).
- O dado de treino é desequilibrado. São 989 golpes bloqueados para 767 honestos atendidos, e só 64 exemplos ensinam a cumprir uma promessa válida, porque é onde o professor mais erra. Antes do resultado, registrei a previsão de que esse vai ser o ponto fraco do modelo ajustado ([ADR 0008](docs/decisoes/0008-gabarito-contestavel.md)).
- 2 dos 212 cenários de teste têm gabarito contestável. Eles ficam na análise principal, e a análise de sensibilidade os exclui.
- O professor às vezes vaza o próprio raciocínio, em inglês, na resposta ao cliente. Isso aparece em 1 das 1.756 conversas de treino.
- O treino fez 1,33 época, com uma semente só. Não sei quanto do resultado muda com outra semente ou com 2 épocas completas.
- A latência e a vazão foram medidas com 8 conversas simultâneas na mesma GPU, esperando o cliente simulado; não são números de produção.
- O custo é estimado: o projeto rodou em camadas gratuitas, e o preço da GPU é o público, com fonte e data.
- Dois setores no treino; o terceiro (varejo) fica para a avaliação de generalização da v1.2.

## Como rodar

```bash
uv sync          # instala as dependências travadas
make check       # lint, tipos e os testes
make scenarios   # gera os cenários de treino e teste (semente fixa)
make samples     # roda o pipeline inteiro com agentes roteirizados, sem GPU
```

O passo a passo completo, do zero até os notebooks no Kaggle, está em [docs/como-rodar.md](docs/como-rodar.md). O mapa do código está em [docs/mapa-do-codigo.md](docs/mapa-do-codigo.md).

## Próximos passos

- v0, para fechar:
  - a ablação sem o filtro do verificador;
  - a comparação com DeepSeek e Gemini pelas APIs;
  - a publicação do modelo, do dataset e da demo no Hugging Face.
- v1.1: DPO com pares "resposta melhor × pior" tirados do próprio verificador, mirando o que o SFT não resolveu:
  - somar o que já foi concedido na conversa (pedido fatiado);
  - transferir só quando a política manda;
  - cumprir promessas válidas.
- v1.2: o setor nunca visto (Loja Tamanduá) e golpes com prova falsa.
- v1.3: auditoria contínua como GitHub Action e o modo "teste o seu agente".

O plano completo, com hipóteses, métricas e regras de corte, está em [docs/plano.md](docs/plano.md).
