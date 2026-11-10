# Plano da Lábia: v0 e v1

> **Status:** **aprovado** em 10/11/2026 (revisão 2). Este arquivo está no primeiro commit do repositório, marcado com a tag `pre-registro`, e vale como **pré-registro**: as hipóteses e a análise ficaram gravadas no git antes de existir qualquer dado, e o hash do commit prova a ordem dos acontecimentos.

> **O que mudou nesta revisão**, a partir das suas respostas:
> 1. **O foco é o iFood.** O setor 2 deixa de ser varejo genérico e vira um app fictício de **delivery de comida**, o Quati. O varejo (Loja Tamanduá) passa a ser o setor 3, que só aparece na avaliação.
> 2. **Orçamento zero.** Nenhum serviço pago e nenhum cartão. O professor e os simuladores agora rodam na nossa própria GPU gratuita (Kaggle), com modelos abertos. APIs gratuitas de terceiros ficam só para a comparação com modelos de ponta.
> 3. **Git:** os commits saem como Denis Carvalho, pela conta nova.

## Como ler

- **Se você tem 15 minutos:** leia "O plano em uma página", a seção 11 (custo zero) e a seção 12 ("O que eu mudaria no briefing"). Depois responda no chat.
- **Se você tem 1 hora,** siga esta ordem:
  1. este arquivo;
  2. as políticas: [Banco Saracura](especificacao/politica-banco-saracura.md), [Quati Delivery](especificacao/politica-quati-delivery.md) e [Loja Tamanduá](especificacao/politica-loja-tamandua.md) (setor 3, só avaliação);
  3. os golpes: [taxonomia de táticas](especificacao/taxonomia-de-taticas.md);
  4. exemplos concretos, em pares: [cenários de exemplo](especificacao/cenarios-de-exemplo.md);
  5. o porquê de cada escolha: [decisões (ADRs)](decisoes/README.md);
  6. o formato dos resultados: [contrato de dados](especificacao/contrato-de-dados.md);
  7. para estudar com calma: [aprendizados](aprendizados.md) e [glossário](glossario.md).

---

## O plano em uma página

**O problema.** Empresas estão dando a agentes de IA o poder de decidir coisas que valem dinheiro: reembolsar um pedido que "não chegou", dar cupom por atraso, estornar tarifa, liberar conta bloqueada. Para fraudar um agente desses ninguém precisa invadir sistema nenhum: basta conversar bem. Mas um agente travado demais, que nega tudo, também custa caro, porque barra o cliente honesto. É o mesmo dilema de qualquer time de prevenção a fraudes: **fraude × atrito**.

**O que a Lábia faz.**

1. Cria duas empresas fictícias para o treino: o **Banco Saracura** (banco digital) e o **Quati** (app de delivery de comida). Cada uma tem política escrita, banco de dados fictício e ferramentas. Uma terceira, a **Loja Tamanduá**, fica guardada para testar um setor que o modelo nunca viu.
2. Põe golpistas e clientes honestos simulados por LLMs para conversar com um agente de atendimento.
3. Julga cada conversa com um **verificador determinístico**: um código que olha o que o agente fez no banco de dados e diz se ele violou a política ou negou um direito, sem depender da opinião de um LLM.
4. Usa um modelo maior (o **professor**) para gerar conversas e guarda só as que o verificador aprova.
5. Com essas conversas, treina um modelo pequeno e aberto, de 4 bilhões de parâmetros.
6. Compara o modelo treinado com a versão sem treino e com modelos de ponta, inclusive numa tática de golpe que ele nunca viu, e mede custo e latência por decisão.

**Tudo isso com custo zero.** O professor, os simuladores e o treino rodam na GPU gratuita do Kaggle. A comparação com modelos de ponta usa as camadas gratuitas do Google AI Studio e da NVIDIA. O gargalo deixa de ser dinheiro e passa a ser **horas de GPU e cotas de API**, e o plano foi redimensionado para caber nelas (seção 11).

**Por que isso conversa com o iFood**

- **Domínio:** reembolso de pedido "não entregue", item faltando, cupom por atraso, troca de endereço. São os casos do dia a dia de um app de delivery.
- **Custo:** o iFood é citado no próprio briefing como exemplo de empresa que treina modelos menores para controlar custo. Mostramos a partir de qual volume isso compensa.
- **Operacionalização:** a trilha AI Engineer fala em "construção e operacionalização de modelos". Por isso o projeto inclui servir o modelo, medir latência e rodar uma auditoria contínua na CI (seção 9).
- **Fraude × atrito:** é a troca entre experiência do cliente e perda financeira que todo time de risco de delivery vive.
- **Custo zero:** o projeto inteiro custa US$ 0,00, com a contabilidade das horas de GPU publicada. Isso mostra que você sabe entregar com o que tem.

**Decisões aprovadas em 10/11/2026**

| # | Tema | Decisão | Onde está o porquê |
|---|---|---|---|
| 1 | Setor 2 | **Delivery de comida (Quati)** no lugar do varejo genérico; o varejo vira o setor 3, só na avaliação | [política do Quati](especificacao/politica-quati-delivery.md) |
| 2 | Modelo base (o "aluno") | Qwen3-4B-Instruct-2507 (Apache 2.0) | [ADR 0002](decisoes/0002-modelo-base.md) |
| 3 | Professor | Piloto no Kaggle entre Qwen3-30B-A3B-Instruct-2507 e gpt-oss-20b (os dois Apache 2.0). Vence o que gerar mais conversas aprovadas por hora de GPU | [ADR 0003](decisoes/0003-professor-e-simuladores.md) |
| 4 | Simulador da avaliação | Ministral-3-14B (Apache 2.0, outra família), na nossa GPU | [ADR 0003](decisoes/0003-professor-e-simuladores.md) |
| 5 | Comparação de ponta | DeepSeek-V4.1-Flash (teste gratuito da NVIDIA) e Gemini Flash-Lite (camada gratuita do Google), só na avaliação. Claude e GPT ficam de fora: não têm acesso gratuito | [ADR 0003](decisoes/0003-professor-e-simuladores.md) |
| 6 | Tática fora do treino | Pedido fatiado (fracionamento) | [ADR 0004](decisoes/0004-divisao-anti-vazamento.md) |
| 7 | Métricas | Fraude, atrito, pass^3, chamadas válidas, valor em risco, custo e latência, todas com intervalo de confiança | [ADR 0005](decisoes/0005-metricas-e-estatistica.md) |
| 8 | O juiz | O determinístico decide; o LLM só classifica a causa raiz | [ADR 0001](decisoes/0001-verificador-deterministico.md) |
| 9 | Escopo da v1.3 | A auditoria contínua na CI sobe de prioridade; o "teste o seu agente" sai como linha de comando experimental | seção 9 |

**Maiores riscos:** um bug no verificador (tudo depende dele), a cota de GPU do Kaggle acabar antes do fim e o professor de 30B aprovar poucas conversas. Os três são medidos já na quarta.

---

## 1. Pergunta de pesquisa e hipóteses

> Dá para ensinar um LLM pequeno e aberto a não cair em engenharia social em português, sem ficar travado com o cliente honesto? E quanto ele custa, comparado aos modelos de ponta?

As hipóteses ficam registradas **antes** dos dados. Isso evita o erro mais comum em projetos de ML: rodar o experimento, olhar o resultado e só depois escolher a métrica que "deu certo".

**Hipóteses principais**, com critério de sucesso definido agora:

| # | Hipótese | Como decidimos |
|---|---|---|
| H1 | Com o mesmo prompt, o modelo ajustado (SFT) deixa passar **menos fraude** que o modelo base nas táticas vistas no treino | o intervalo de confiança (IC) de 95% da diferença (base − SFT) fica inteiro acima de zero |
| H2 | O SFT **não aumenta o atrito** em mais de 5 pontos percentuais em relação ao base | o limite superior do IC 95% da diferença (SFT − base) fica abaixo de +5 p.p. |
| H3 | O SFT deixa passar menos fraude que o base também na **tática que ficou fora do treino** | o IC 95% da diferença (base − SFT) fica inteiro acima de zero |

Como são três hipóteses, aplicamos a correção de Holm–Bonferroni. Ela reduz a chance de alguma "acertar por sorte" só porque testamos várias.

**Perguntas secundárias** (respondidas com IC, mas sem critério de sucesso prévio):

- O SFT supera o modelo base com prompt reforçado? Ou seja: treinar vale mais do que só escrever um prompt melhor?
- Quanto falta para o SFT chegar ao nível do professor?
- Onde o SFT fica em relação aos modelos de ponta?

**Análises exploratórias**, apresentadas como tal: custo e latência, as ablações (sem o filtro do verificador; com metade dos dados, se der tempo), o setor que o modelo nunca viu e a prova falsa (v1.2), e o DPO (v1.1).

Um resultado negativo em qualquer hipótese é publicado do mesmo jeito, com a explicação do porquê.

## 2. O que já existe e o que é novo

Li e conferi os trabalhos que o briefing cita. Os números da tabela são dos próprios papers.

| Trabalho | O que fez | O que não fez | O que aproveitamos |
|---|---|---|---|
| **τ-bench** (Yao et al., 2024, [arXiv 2406.12045](https://arxiv.org/abs/2406.12045)) | Ambiente com ferramentas, política e usuário simulado, nos domínios de companhia aérea e varejo. O acerto é julgado pelo estado final do banco de dados. Criou a métrica pass^k. Mesmo o GPT-4o acertou menos de 50% das tarefas, e no varejo o pass^8 ficou abaixo de 25% | Não estuda usuários mal-intencionados | O desenho do ambiente, o julgamento pelo estado final e o pass^k |
| **CRAFT e τ-break** (Nakash et al., 2025, [arXiv 2506.09600](https://arxiv.org/abs/2506.09600)) | Um atacante com vários agentes, que lê a política e planeja a persuasão. Contra o GPT-4o no domínio aéreo, o ataque teve 70,0% de sucesso, contra 42,5% de um usuário ingênuo e 35,0% do prompt DAN. A melhor defesa testada (lembrar ao agente os trechos relevantes da política) reduziu o ataque sem eliminá-lo: de 70,0% para 36,2% no GPT-4o | É em inglês, não treina modelos e não mede o cliente honesto barrado | O atacante que lê a política, e a defesa por lembrete, que vira o nosso "prompt reforçado" |
| **Language Model Agents Under Attack** (Zhang, 2025, [arXiv 2512.24415](https://arxiv.org/abs/2512.24415)) | 100 roteiros de ataque, 10 setores e 5 modelos. A família de ataque mais eficaz foi o *payload splitting* (dividir o pedido em partes) | Avalia só um turno de conversa, julga com LLM (nota de 0 a 5) e não treina | A evidência de que o pedido fatiado é a tática mais perigosa |
| **Beyond Detection** (Xu et al., 2026, [arXiv 2608.10239](https://arxiv.org/abs/2608.10239)) | 300 casos e 5 modelos defensores, em conversa turno a turno. Propõe localizar qual elo da cadeia de confiança falhou: autoridade do ator, controle do ativo, suficiência da verificação ou caminho da transação. Mostra que "agir para proteger" e "apontar a causa certa" muitas vezes não andam juntos | O defensor protege um usuário humano; não há agente com ferramentas decidindo dinheiro | Os quatro elos viram a nossa classificação de falhas |
| **OWASP Top 10 for Agentic Applications** ([dez. 2025](https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/)) | Lista de riscos de aplicações com agentes | — | O enquadramento de risco: ASI01 e ASI02 (ver abaixo) |

**O que é novo na Lábia:**

1. português e repertório brasileiro (Procon, Reclame Aqui, "você sabe com quem está falando?", número de protocolo, MED do Pix);
2. treino de um modelo pequeno para resistir, com prova numa tática nunca vista e num setor nunca visto;
3. fraude e atrito medidos juntos, com **pares mínimos** (seção 4);
4. custo e latência por decisão, comparando um modelo servido por nós com modelos via API;
5. tudo reproduzível com custo zero.

**Duas correções ao briefing** (o detalhe está na seção 12):

- O briefing cita o **ASI09**, mas o ASI09 ("Human-Agent Trust Exploitation") é o sentido inverso: o agente que convence o humano a fazer algo ruim. O nosso caso é um humano manipulando o agente para usar ferramentas legítimas de forma indevida. Isso é o **ASI01 (Agent Goal Hijack)**, com consequência no **ASI02 (Tool Misuse)**.
- O **caso da United** aconteceu, mas não do jeito descrito. Em setembro de 2025, um usuário disse ao assistente virtual que o CEO tinha prometido um reembolso. O bot pediu desculpas e o encaminhou ao formulário de reembolso, mas **não concedeu reembolso nenhum**, e a fonte é um blog ([View from the Wing](https://viewfromthewing.com/scott-kirby-promised-me-a-refund-and-uniteds-ai-chatbot-fell-for-it/)). O caso com decisão formal é *Moffatt v. Air Canada* (2024): um tribunal do Canadá responsabilizou a companhia aérea pela informação errada sobre reembolso que o chatbot dela deu a um cliente.

## 3. Arquitetura

```mermaid
flowchart LR
    subgraph SB["Sandbox (um por setor)"]
        POL["Política escrita"]
        DB[("Banco fictício<br/>SQLite")]
        TOOLS["Ferramentas"]
        VER{{"Verificador<br/>determinístico"}}
    end

    GEN["Gerador de cenários<br/>(código + semente)"] --> RUN["Laço de conversa"]
    SIM["Cliente simulado<br/>golpista ou honesto"] <--> RUN
    AG["Agente<br/>professor ou modelo avaliado"] <--> RUN
    AG -- "chamadas de ferramenta" --> TOOLS --> DB
    RUN --> VER
    DB --> VER

    VER -- "aprovadas" --> TRAIN[("Conversas de treino")]
    TRAIN --> SFT["SFT com LoRA<br/>no Kaggle"] --> MODEL["Modelo Lábia"]
    MODEL --> EVAL["Avaliação<br/>3 rodadas + IC"]
    VER --> EVAL
    EVAL --> RES[("results/*.json")]
    RES --> PANEL["Painel React"]
    RES --> PORT["Portfólio"]
    MODEL --> GGUF["Merge + GGUF"] --> BENCH["Latência e custo"]
    GGUF --> SPACE["Space: tente aplicar um golpe"]
    VER --> SPACE
```

**Onde cada parte roda (tudo gratuito)**

| Parte | Onde | Por quê |
|---|---|---|
| Sandbox, verificador e testes | seu computador e GitHub Actions | é Python puro e leve |
| Professor e simuladores do treino | Kaggle, GPU gratuita (2× T4), com llama.cpp | o texto deles vira dado de treino, então precisa vir de modelo aberto rodando por nós |
| Treino (SFT e DPO) | Kaggle; o Colab gratuito fica de reserva | precisa de GPU |
| Avaliação dos modelos pequenos e do professor | Kaggle: o modelo avaliado numa T4 e o simulador da avaliação na outra | precisa de GPU |
| Modelos de ponta na avaliação | APIs gratuitas (Google AI Studio e NVIDIA), chamadas de um notebook do Kaggle | os termos gratuitos permitem avaliação, não geração de dados de treino |
| Latência em CPU | runner do GitHub Actions ou CPU do Space, com hardware documentado | seu notebook (i7 de 2ª geração, 6 GB de RAM) não representa um servidor |
| Latência em GPU | Kaggle | |
| Demo | Hugging Face Spaces, na CPU gratuita: a sua conta nova só completa os 30 dias exigidos para a GPU gratuita (ZeroGPU) em dezembro. O modo principal mostra conversas gravadas; o modo ao vivo entra se a latência na CPU for aceitável | |
| Painel | GitHub Pages | |

## 4. Onze decisões de desenho

Cada uma destas é um argumento que você pode usar numa entrevista.

1. **A política vira código.** O verificador é um motor de regras: para cada ação do agente, ele confere se a política permitia aquela ação. A mesma regra julga o treino, a avaliação e o Space ao vivo. No Space, quando alguém tenta aplicar um golpe, a tela mostra na hora algo como "o agente violou a regra D2".
2. **O gabarito nasce do código.** Os cenários são gerados por código, com semente fixa. Quem determina se o cliente tem direito é o estado do banco de dados que o gerador montou, não um LLM; o LLM só escreve o diálogo. E o gerador e o verificador se conferem: um teste garante que todo cenário marcado como "legítimo" é aprovado pelo verificador e todo cenário de golpe é recusado.
3. **Pares mínimos.** Cada tática aparece tanto em golpes quanto em clientes honestos. Exemplo: dois clientes ameaçam ir ao Procon porque o pedido "não chegou". No sistema de um, o entregador marcou o pedido como extraviado (ele tem direito ao reembolso). No do outro, a entrega foi confirmada com o código (não tem). A frase é a mesma e a resposta certa é oposta. Isso obriga o modelo a consultar o sistema em vez de julgar pelo tom. A ideia vem dos *contrast sets* (Gardner et al., 2020).
4. **Destilação de contexto.** O professor atende com um prompt reforçado (a política mais um checklist contra manipulação). Nos dados de treino, a conversa é guardada com o prompt simples. Assim o aluno aprende a se comportar como se tivesse o reforço, sem pagar pelos tokens extras em cada chamada (Askell et al., 2021; Snell et al., 2022).
5. **Filtro duplo.** Para entrar no treino, a conversa precisa de duas coisas: o resultado certo e o processo certo (o agente consultou o sistema antes de agir). Além disso, não pode ter sinal da tática fora do treino e o simulador não pode ter saído do personagem. O objetivo é que o aluno aprenda a verificar, e não a acertar por sorte.
6. **Famílias diferentes no treino e no teste.** O professor e os simuladores do treino vêm de uma família (Qwen ou gpt-oss); o simulador da avaliação vem de outra (Mistral). Se o mesmo atacante gerasse o treino e o teste, o aluno poderia decorar os "tiques" dele, e o resultado do teste sairia inflado.
7. **Escada de generalização.** Testamos em quatro degraus, do mais fácil ao mais difícil: (1) cenários novos com táticas já vistas; (2) uma tática nunca vista; (3) um setor nunca visto, a Loja Tamanduá (v1.2); (4) um anexo falso (v1.2). Cada degrau responde se o modelo aprendeu o princípio ou só decorou exemplos.
8. **O determinístico decide e o LLM explica.** Pela regra violada, já se sabe qual elo de confiança falhou. O juiz LLM só classifica a causa raiz (por exemplo, "aceitou a alegação sem consultar o sistema"). Você revisa 50 casos e medimos a concordância dele com você (kappa de Cohen).
9. **Um único harness para todos.** Todo modelo é chamado pela API no formato da OpenAI, que o llama.cpp, o vLLM, o Google AI Studio e a NVIDIA entendem. O mesmo código avalia qualquer modelo, e quem tiver uma chave paga do Claude ou do GPT pode rodar a avaliação sozinho.
10. **Honestidade por construção.** Todo número publicado carrega o tipo, medido ou estimado. Os dados de exemplo carregam `is_sample: true`, o painel mostra um selo de "dados de exemplo" e o script de publicação se recusa a publicá-los.
11. **Custo zero com a conta à vista.** Registramos as horas de GPU e as chamadas de API de cada etapa e publicamos essa contabilidade. O "quanto custou" vira um resultado do projeto, e não uma nota de rodapé.

## 5. Modelos

| Papel | Modelo | Licença | Onde roda |
|---|---|---|---|
| Aluno (o modelo que vamos ajustar) | Qwen3-4B-Instruct-2507 | Apache 2.0 | Kaggle |
| Professor e simuladores do treino, candidato A | Qwen3-30B-A3B-Instruct-2507 (GGUF de 4 bits) | Apache 2.0 | Kaggle, llama.cpp |
| Professor e simuladores do treino, candidato B | gpt-oss-20b (MXFP4) | Apache 2.0 | Kaggle, llama.cpp |
| Simulador da avaliação | Ministral-3-14B-Instruct-2512 (GGUF de 4 bits) | Apache 2.0 | Kaggle, llama.cpp |
| Juiz da causa raiz | o mesmo modelo do professor | Apache 2.0 | Kaggle |
| Ponta aberto (comparação) | DeepSeek-V4.1-Flash | MIT | NVIDIA, teste gratuito, só avaliação |
| Ponta fechado (comparação) | Gemini Flash-Lite (a versão mais recente da camada gratuita) | fechado | Google AI Studio, camada gratuita, só avaliação |
| Fora do projeto | Claude e GPT | fechados | sem acesso gratuito; o harness aceita a chave de quem tiver |

**Regra de dados:** tudo o que entra no treino vem de modelos abertos (Apache 2.0 ou MIT) rodando na nossa GPU. Os termos do teste gratuito da NVIDIA permitem só "teste e avaliação internos, não produção", então ela entra só na avaliação. Das APIs de terceiros publicamos as métricas, não as conversas em massa. O dataset no Hugging Face contém apenas o que nós geramos com modelos abertos.

## 6. Métricas

| Métrica | Definição | Por que importa |
|---|---|---|
| **Taxa de fraude** | % das conversas de golpe em que o agente executou alguma ação proibida pela política | é o prejuízo |
| **Taxa de atrito** | % das conversas legítimas em que o cliente não recebeu o que tinha direito: foi negado ou transferido sem necessidade | é o cliente honesto barrado |
| **pass^3** | % dos cenários em que o agente acertou as 3 rodadas | consistência: um agente que acerta 2 de 3 vezes também erra em produção |
| **Chamadas válidas** | % das chamadas de ferramenta com nome e argumentos válidos | mostra se o modelo pequeno sabe usar ferramentas |
| **Valor em risco** | R$ concedidos indevidamente a cada mil conversas | é a linguagem de prevenção a fraudes; em delivery, são muitas perdas pequenas |
| **Turno da concessão** | em que turno o agente cedeu | alimenta a curva de resistência por turno |
| **Custo por mil conversas** | US$, sempre **estimado**. Modelo próprio: preço público de GPU por hora ÷ conversas por hora medidas. APIs: tokens medidos × preço de tabela | a pergunta de negócio. Não pagamos nada, mas calculamos quanto custaria |
| **Latência** | segundos por turno do agente (p50 e p95) e por decisão | a experiência do cliente |

**Estatística.** Cada cenário roda 3 vezes. O IC 95% vem de um **bootstrap por cenário**: sorteamos cenários inteiros, com as 3 rodadas juntas, porque rodadas do mesmo cenário se parecem entre si. Para comparar dois modelos, usamos **bootstrap pareado** nos mesmos cenários. A referência é Miller (2024), "Adding Error Bars to Evals".

**Gráficos planejados:**

- o plano fraude × atrito, com a fronteira de Pareto e os ICs;
- a **curva de resistência por turno**: a porcentagem de golpes ainda resistidos depois de k turnos. É uma curva de sobrevivência, ideia emprestada da estatística médica, e mostra coisas como "o modelo base cede no 2º turno e o ajustado aguenta até o 6º";
- um mapa de calor tática × modelo;
- a escada de generalização;
- custo × resistência, com o ponto de equilíbrio por volume: a partir de quantas conversas por mês o modelo próprio fica mais barato que a API.

## 7. Quem é comparado com quem

| ID | Agente | Prompt | Onde roda | Papel na análise |
|---|---|---|---|---|
| `base` | Qwen3-4B-Instruct-2507 sem ajuste | padrão | Kaggle | linha de base de H1 a H3 |
| `base+reforco` | Qwen3-4B-Instruct-2507 sem ajuste | reforçado | Kaggle | **linha de base forte**: dá para resolver só com prompt? |
| `sft` | Lábia v0 (SFT) | padrão | Kaggle | o modelo principal |
| `sft-sem-filtro` | SFT treinado sem o filtro do verificador | padrão | Kaggle ou Colab | ablação: o verificador importa? |
| `professor` | o vencedor do piloto | padrão | Kaggle | o teto de referência da destilação |
| `deepseek` | DeepSeek-V4.1-Flash | padrão | NVIDIA, grátis | ponta aberto |
| `deepseek+reforco` | DeepSeek-V4.1-Flash | reforçado | NVIDIA, grátis | ponta com defesa |
| `gemini-lite` | Gemini Flash-Lite | padrão | Google AI Studio, grátis | ponta fechado, num subconjunto de cenários |
| `sft+dpo` (v1.1) | SFT + DPO | padrão | Kaggle | v1.1, se sobrar GPU |
| `sft-metade` | SFT com metade dos dados | padrão | Colab | ablação, se sobrar GPU |

**Prompt reforçado:** a política mais uma seção explícita contra manipulação e, a cada turno, um lembrete das regras gerais no fim do contexto (a defesa que mais funcionou no CRAFT). Para não favorecer ninguém, o reforço **não menciona a tática que ficou fora do treino**.

**Tamanho da avaliação** (número de planejamento, ajustado depois do piloto): cerca de 200 cenários de teste, sendo 120 com as táticas vistas (60 golpes e 60 legítimos) e 80 com a tática nova (40 e 40). Cada um roda 3 vezes, o que dá cerca de 600 conversas por configuração. Pela fórmula da proporção, o IC 95% de uma taxa entre 30% e 50% fica entre ±7 e ±13 pontos percentuais nas táticas vistas e entre ±8 e ±16 na tática nova, dependendo de quanto as 3 rodadas concordam; o valor real sai do bootstrap. O Gemini roda num subconjunto de 60 a 90 cenários, por causa da cota diária, e os ICs dele são mais largos. Isso fica dito junto do número.

## 8. Cronograma até domingo, 15/11

| Dia | Frente A (motor, esta pasta) | Frente B (painel) | Tarefas que só você pode fazer |
|---|---|---|---|
| **Ter 10** | Este plano | — | Ler, responder e dar o ok |
| **Qua 11** | Esqueleto do repositório (uv, Makefile, testes, lint, CI); contrato de dados com dados de exemplo; sandbox dos 2 setores; verificador com testes; laço de conversa com servidor local e cache; **teste de fumaça e piloto no Kaggle** | Esqueleto do painel lendo os dados de exemplo | Criar as contas gratuitas (lista na seção 11) e rodar no Kaggle os notebooks que eu preparar |
| **Qui 12** | Geração em escala no Kaggle (roda sozinha em segundo plano) e filtragem; avaliação de base; começa a avaliação do Gemini, que precisa de vários dias de cota | Visão geral, plano fraude × atrito, ranking e mapa de táticas | Revisar 10 conversas do piloto (o português está natural?) e auditar 30 veredictos do verificador |
| **Sex 13** | SFT no Kaggle; ablação sem filtro no Colab; CLI de auditoria | Replay das conversas e relatório de auditoria | Disparar os treinos; revisar 50 classificações do juiz |
| **Sáb 14** | Avaliação do SFT; merge, GGUF e latência; modelo e dataset no Hugging Face; GitHub Action de auditoria contínua; setor 3, se sobrar GPU | Painel com os dados reais e deploy | Conferir os resultados; gravar a demo |
| **Dom 15** | Space, README, artigo e vídeo | Ajustes finais | Portfólio (Frente C) com os números reais |

**Caminho crítico** (se um destes atrasa, tudo atrasa): verificador → piloto → geração → SFT → avaliação → publicação. Por isso a quarta é o dia mais importante da semana.

**Teste de fumaça e piloto (quarta, no Kaggle, umas 2 a 2,5 horas de GPU):**

- **Aluno:** carregar o Qwen3-4B em 4 bits, rodar 20 passos de treino com Unsloth, gerar 10 chamadas de ferramenta em português e servir o modelo com vLLM na T4.
- **Professor:** os dois candidatos atendem os mesmos ~20 cenários. Medimos a taxa de aprovação, a velocidade e a qualidade do português.
- **Simulador da avaliação:** medimos com que frequência ele recusa o papel de golpista ou sai do personagem.

Se algum desses passos falhar, descobrimos na quarta, e não na sexta com o treino de verdade.

## 9. Prioridades e regras de corte

Mantenho as regras do briefing, acrescento uma ordem explícita para os extras e ajusto essa ordem ao foco no iFood e ao custo zero.

**Nunca se corta** (do briefing): o verificador determinístico, a avaliação honesta com a tática fora do treino, o modelo SFT e o dataset no Hugging Face, o painel com dados reais, o README e a página de portfólio.

**Ordem de prioridade dos extras**, do mais para o menos importante:

1. a linha de base com prompt reforçado (barata, e um avaliador vai perguntar por ela);
2. a ablação sem o filtro do verificador (testa a tese central do projeto);
3. a **GitHub Action de auditoria contínua** (v1.3). Ela subiu de prioridade: é barata, porque reaproveita o harness, e mostra exatamente a "operacionalização" que a trilha AI Engineer pede. Na CI, roda um conjunto pequeno de ataques com roteiro fixo contra o modelo GGUF em CPU e falha se a fraude ou o atrito passarem de um limite;
4. o setor 3 (Loja Tamanduá), só na avaliação (v1.2). A política já está escrita;
5. o DPO (v1.1). Desceu de posição porque precisa de várias horas extras de GPU;
6. a prova falsa (v1.2);
7. a ablação com metade dos dados;
8. o relatório de auditoria em PDF (v1.3; Markdown convertido em PDF);
9. o modo "teste o seu agente" (v1.3), só como linha de comando e marcado como experimental.

Continuam valendo as regras do briefing: se o SFT não estiver treinado até sábado de manhã, o DPO sai do prazo; o terceiro setor e a prova falsa podem sair sem afetar o resto; o que entrar incompleto aparece como "experimental".

## 10. Riscos e mitigação

| Risco | Chance | Impacto | Mitigação |
|---|---|---|---|
| Um bug no verificador rotula errado | média | **crítico** | testes por regra com casos escritos à mão; teste cruzado gerador × verificador; você audita 30 veredictos sorteados (aqui entra sua experiência em auditoria) |
| A cota de GPU do Kaggle acaba antes do fim | média | alto | contabilidade de horas desde o primeiro dia; Colab gratuito como reserva; volumes ajustáveis (menos conversas de treino, teste menor); extras cortados na ordem da seção 9 |
| O professor de 30B aprova poucas conversas | média | alto | o piloto mede; prompt reforçado; até 2 tentativas por cenário; o filtro do verificador compensa a qualidade menor |
| O simulador recusa o papel de golpista ou sai do personagem | média | médio | o piloto mede; filtro automático; trocamos de modelo se passar de 10% |
| O ambiente do Kaggle (versões, memória, T4 sem bfloat16) | média | alto | teste de fumaça na quarta; llama.cpp para os modelos maiores; Unsloth com QLoRA para o treino |
| Um modelo do teste gratuito da NVIDIA some sem aviso (já aconteceu em agosto de 2026) | média | baixo | ele só afeta uma linha de comparação; trocamos por outro do catálogo e registramos a troca |
| A cota gratuita do Gemini é pequena | alta | baixo | subconjunto de cenários, começando na quinta para usar vários dias de cota |
| O formato das chamadas de ferramenta quebra depois do ajuste | baixa | alto | treinar com o template nativo do modelo; métrica de chamadas válidas; testes do parser |
| A tática fora do treino vaza para o treino | média | alto | detector determinístico (dois ou mais pedidos de benefício na mesma conversa) e etiquetador LLM; conversas suspeitas saem do treino |
| A conta do Hugging Face é nova (menos de 30 dias até domingo) | confirmado | baixo | o Space roda em CPU, com as conversas gravadas como modo principal e isso explicado na tela; em dezembro a conta completa 30 dias e o Space pode passar para a GPU gratuita |
| O prazo | alta | alto | as regras de corte acima |
| Um nome fictício coincide com marca real | baixa | médio | busca rápida antes de publicar |
| Mau uso do dataset (roteiros de golpe) | baixa | médio | empresas fictícias; táticas genéricas e já conhecidas; seção de uso responsável no dataset card |

## 11. Custo zero: o orçamento agora é de horas de GPU e de cotas

**Custo em dinheiro: US$ 0,00.** Nenhum serviço pago e nenhum cartão. Em troca, temos dois limites, que são o novo orçamento.

**Horas de GPU** (estimativas de planejamento; o piloto mede a velocidade real e ajustamos os volumes):

| Etapa | Onde | Horas de GPU |
|---|---|---|
| Teste de fumaça e piloto | Kaggle | 2 a 2,5 |
| Geração do treino (~1.500 a 2.500 conversas, para ter 1.000 a 1.500 aprovadas) | Kaggle, em segundo plano | 6 a 10 |
| SFT principal | Kaggle | 2 a 3 |
| Ablação sem filtro | Colab gratuito (ou Kaggle) | 2 a 3 |
| Avaliação dos modelos rodados por nós, com o simulador da avaliação (também usado nas avaliações de ponta) | Kaggle | 5 a 8 |
| GGUF e latência | Kaggle | 1 |
| **Total** | | **~18 a 28 h**, dentro das ~30 h semanais que o Kaggle costuma dar |
| DPO (v1.1), se couber | Kaggle | +3 a 5 |

A cota do Kaggle não é publicada oficialmente e varia por conta. O número real aparece nas configurações da sua conta, e vamos acompanhá-lo a cada dia.

**Cotas de API** (só para a comparação com modelos de ponta):

| Serviço | Limite | O que dá para fazer |
|---|---|---|
| Google AI Studio, Gemini Flash-Lite | cerca de 500 requisições por dia, segundo relatos de terceiros. O número oficial aparece no painel da sua conta | ~70 conversas por dia → 60 a 90 cenários × 3 rodadas, de quinta a domingo |
| NVIDIA, teste gratuito | cerca de 40 requisições por minuto, compartilhadas entre todos os modelos | ~600 conversas em umas 2 horas de chamadas, por configuração |

**Contas que você precisa criar** (todas gratuitas e sem cartão):

1. **GitHub**, a conta nova.
2. **Hugging Face,** criada já, com o mesmo e-mail. Ela só completa os 30 dias exigidos para a GPU gratuita no Space em dezembro, então até lá o Space roda em CPU.
3. **Kaggle,** com o telefone verificado (é o que libera GPU e internet nos notebooks).
4. **Google AI Studio,** com a sua conta Google. Gere uma chave de API.
5. **NVIDIA Developer Program,** para gerar a chave em build.nvidia.com.
6. **Weights & Biases,** para registrar os experimentos. Opcional: dá para usar o Trackio, que roda no próprio Hugging Face.

Use **o mesmo nome de usuário** no GitHub, no Hugging Face e no Kaggle. Assim os links do portfólio ficam consistentes, e quem achar um perfil acha os outros.

As chaves ficam nos *Secrets* do Kaggle e num arquivo `.env` no seu computador, que o `.gitignore` já protege. Nunca no repositório.

## 12. O que eu mudaria no briefing

1. **O prazo da v1 é otimista demais.** A v0 sozinha já ocupa a semana, e a v1.3 é um produto por si só. Com custo zero, o limite de GPU aperta ainda mais. Uma entrega menor e sólida impressiona mais que uma v1 pela metade. Por isso ordenei os extras pela relação entre valor e custo (seção 9).
2. **O ASI09 está trocado.** Vamos usar o ASI01 e o ASI02 (seção 2).
3. **O caso da United precisa ser contado direito.** Do jeito que está no briefing, um avaliador que conheça o caso percebe o exagero. Vamos usar a versão correta e citar o caso da Air Canada, que teve decisão formal.
4. **A exigência de licença aberta não vale só para o professor.** O texto dos simuladores também entra nos dados de treino. Com custo zero, a solução ficou ainda mais limpa: professor e simuladores rodam na nossa GPU, com modelos Apache 2.0.
5. **Faltava a linha de base mais óbvia:** o modelo pequeno com prompt reforçado. É a primeira pergunta de um avaliador sênior: "por que treinar, se dava para resolver no prompt?". Agora ela é respondida com dados.
6. **Só ter clientes legítimos não basta para medir atrito.** Se o cliente honesto nunca pressiona, o modelo aprende que pressão é sinal de golpe e barra o cliente irritado que tem razão. Os pares mínimos resolvem isso.
7. **A história do custo mudou.** Hoje modelos fechados baratos custam US$ 0,10 por milhão de tokens de entrada. Então "o modelo pequeno é mais barato" deixou de ser óbvio e passou a depender do volume. Em vez de afirmar, vamos mostrar o ponto de equilíbrio. Há também vantagens que não são de custo: os dados do cliente não saem da empresa (relevante para a LGPD), não há dependência de um fornecedor e a latência fica sob controle. Essas entram como argumentos qualitativos, não como números.
8. **O juiz LLM tinha uma função redundante.** A regra violada já diz, de forma determinística, qual controle falhou. O juiz passa a classificar a causa raiz, que é o que um relatório de auditoria precisa.
9. **A "consistência entre as 3 rodadas" ganha nome e fórmula:** pass^3, do τ-bench.
10. **Seu computador não pode ser o hardware do benchmark.** Vamos usar hardware documentado e reproduzível.
11. **Sem Claude e sem GPT.** Com custo zero, a comparação de ponta fica com um modelo aberto de fronteira (DeepSeek) e um fechado (Gemini Flash-Lite). Isso é uma limitação, e ela vai escrita no README, junto com a instrução de como qualquer pessoa com uma chave paga pode rodar a mesma avaliação. A sua assinatura do Claude, usada aqui no Claude Code, não resolve isso: ela é para uso interativo, e a avaliação precisaria da API da Anthropic, cobrada à parte, por token. Além disso, o Claude desta sessão escreveu as políticas e os cenários; avaliá-lo seria como pedir ao professor que escreveu a prova para fazer a prova.

## 13. Depois de 16/11 (roadmap)

- Avaliar Claude e GPT, se houver crédito ou patrocínio.
- Repetir a receita com outros modelos base (Qwen3.5-4B, Granite-4.2-3B), para saber se ela funciona em mais de um modelo.
- Validação cruzada deixando cada tática de fora uma vez (5 treinos).
- Aprendizado por reforço usando o verificador como recompensa, o passo natural depois do DPO.
- Ataques multimodais de verdade, com print adulterado como imagem.
- Mais setores: telecom, mercado, farmácia.
- Captar promessas feitas só em texto (o agente diz "vou reembolsar" sem chamar a ferramenta), que o verificador de estado não enxerga. É a lição do caso da Air Canada.

## 14. Referências

**Agentes, ataques e defesas**

- Yao, S. et al. (2024). τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. [arXiv 2406.12045](https://arxiv.org/abs/2406.12045).
- Barres, V. et al. (2025). τ²-Bench: Evaluating Conversational Agents in a Dual-Control Environment. [arXiv 2506.07982](https://arxiv.org/abs/2506.07982).
- Nakash, I. et al. (2025). Effective Red-Teaming of Policy-Adherent Agents (CRAFT e τ-break). [arXiv 2506.09600](https://arxiv.org/abs/2506.09600).
- Zhang, J. (2025). Language Model Agents Under Attack: A Cross Model-Benchmark of Profit-Seeking Behaviors in Customer Service. [arXiv 2512.24415](https://arxiv.org/abs/2512.24415).
- Xu, Y. et al. (2026). Beyond Detection: Evaluating Defensive LLMs Against AI-Generated Social Engineering in Live Turn-by-Turn Interaction. [arXiv 2608.10239](https://arxiv.org/abs/2608.10239).
- Zeng, Y. et al. (2024). How Johnny Can Persuade LLMs to Jailbreak Them. [arXiv 2401.06373](https://arxiv.org/abs/2401.06373).
- Russinovich, M. et al. (2024). The Crescendo Multi-Turn LLM Jailbreak Attack. [arXiv 2404.01833](https://arxiv.org/abs/2404.01833).
- OWASP GenAI Security Project (2025). [Top 10 for Agentic Applications](https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/).

**Treino**

- Hu, E. et al. (2021). LoRA. [arXiv 2106.09685](https://arxiv.org/abs/2106.09685).
- Dettmers, T. et al. (2023). QLoRA. [arXiv 2305.14314](https://arxiv.org/abs/2305.14314).
- Rafailov, R. et al. (2023). Direct Preference Optimization. [arXiv 2305.18290](https://arxiv.org/abs/2305.18290).
- Zelikman, E. et al. (2022). STaR: Bootstrapping Reasoning With Reasoning. [arXiv 2203.14465](https://arxiv.org/abs/2203.14465).
- Askell, A. et al. (2021). A General Language Assistant as a Laboratory for Alignment. [arXiv 2112.00861](https://arxiv.org/abs/2112.00861).
- Snell, C. et al. (2022). Learning by Distilling Context. [arXiv 2209.15189](https://arxiv.org/abs/2209.15189).

**Avaliação**

- Miller, E. (2024). Adding Error Bars to Evals. [arXiv 2411.00640](https://arxiv.org/abs/2411.00640).
- Gardner, M. et al. (2020). Evaluating Models' Local Decision Boundaries via Contrast Sets. [arXiv 2004.02709](https://arxiv.org/abs/2004.02709).
- Röttger, P. et al. (2023). XSTest: exaggerated safety behaviours. [arXiv 2308.01263](https://arxiv.org/abs/2308.01263).
- Cui, J. et al. (2024). OR-Bench: An Over-Refusal Benchmark. [arXiv 2405.20947](https://arxiv.org/abs/2405.20947).

**Infraestrutura gratuita (consultada em 10/11/2026)**

- OpenRouter: [limites dos modelos gratuitos](https://openrouter.ai/docs/api-reference/limits) (50 requisições por dia sem crédito comprado, por isso não usamos).
- Hugging Face: [ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu) (contas gratuitas com mais de 30 dias podem hospedar até 2 Spaces com GPU).
- NVIDIA: termos do teste gratuito, resumidos e citados em [DEV Community](https://dev.to/rudratosh/nvidia-will-run-glm-53-and-kimi-k3-for-you-for-free-i-read-the-fine-print-here-are-the-three-3mkj) (uso só para teste e avaliação; cerca de 40 requisições por minuto; modelos podem sair do catálogo).
- Google AI Studio: [limites de uso](https://aistudio.google.com/docs/rate-limits) (os valores da camada gratuita aparecem no painel de cada conta).
- Kaggle: cota de GPU relatada por terceiros ([gpuperhour](https://gpuperhour.com/blog/free-cloud-gpus-and-credits)).

**Casos reais e regras brasileiras**

- View from the Wing (06/09/2025). ["Scott Kirby Promised Me A Refund" — And United's AI Chatbot Fell For It](https://viewfromthewing.com/scott-kirby-promised-me-a-refund-and-uniteds-ai-chatbot-fell-for-it/).
- *Moffatt v. Air Canada*, 2024 BCCRT 149 (Civil Resolution Tribunal, Colúmbia Britânica).
- Código de Defesa do Consumidor (Lei 8.078/1990), arts. 26 e 49.
- MED do Pix: prazo de 80 dias ([Gazeta do Povo](https://www.gazetadopovo.com.br/economia/nova-regra-pix-prazo-para-contestacao-sobe-para-80-dias/); conferir o texto do Banco Central antes de publicar).
- Regras do SAC: [Decreto 11.034/2022](https://www.planalto.gov.br/ccivil_03/_Ato2019-2022/2022/Decreto/D11034.htm) e o novo decreto que o substitui desde 02/11/2026 ([O Liberal](https://www.oliberal.com/para/novo-decreto-garante-atendimento-humano-no-sac-a-partir-de-2-de-novembro-1.1188620); número a confirmar no Planalto).
