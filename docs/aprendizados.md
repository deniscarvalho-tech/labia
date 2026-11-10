# Diário de aprendizados

> Um registro por etapa: o que foi feito e por quê, os conceitos em português simples, as alternativas descartadas e as perguntas que um entrevistador faria. Termos técnicos têm definição curta no [glossário](glossario.md).

---

## Etapa 0: planejamento (terça, 10/11/2026)

### O que foi feito

1. Lemos o briefing inteiro e transcrevemos o PDF para o `BRIEFING.md`.
2. Conferimos na fonte as referências do briefing. Os quatro papers existem e dizem o que o briefing diz. Duas afirmações, porém, estavam imprecisas: o OWASP ASI09 (é o sentido inverso do nosso caso) e o caso da United (o bot não deu o reembolso).
3. Pesquisamos os modelos disponíveis hoje (novembro de 2026) nas fontes primárias: a API pública da OpenRouter, para os preços, e a API do Hugging Face, para licença, tamanho e arquitetura de cada modelo. Não usamos memória nem blogs, porque essas informações mudam todo mês.
4. Escrevemos o plano, as duas políticas, a taxonomia de táticas, os cenários de exemplo, o contrato de dados e cinco ADRs.

### Por que foi feito assim

Em ML, o erro mais caro é descobrir no fim que a avaliação mediu a coisa errada. Normalmente ninguém percebe até alguém de fora perguntar: "como você sabe que o modelo não decorou o teste?". As decisões de hoje (verificador, pares mínimos, tática fora do treino, simuladores diferentes no treino e no teste) é que vão tornar o resultado crível. Código errado se reescreve em uma hora; um experimento mal desenhado só se descobre depois de gastar a semana inteira.

Pelo mesmo motivo, conferimos as fontes. O briefing é cuidadoso, mas tinha dois erros factuais. Se eles chegassem ao artigo, um leitor atento perceberia e passaria a duvidar do resto.

### Conceitos

#### LLM e token

Um LLM (*Large Language Model*, modelo de linguagem grande) é um programa que recebe um texto e prevê o pedaço mais provável de vir a seguir, uma vez depois da outra. Pense no autocompletar do celular, só que treinado numa quantidade enorme de texto e com bilhões de parâmetros (os números que o treino ajusta).

O **token** é a unidade que o modelo lê e escreve: uma palavra curta ou um pedaço de palavra ("estorno" pode virar dois tokens). As APIs cobram por milhão de tokens, com preços separados para a entrada (o que você manda) e a saída (o que o modelo escreve).

#### Agente e chamada de ferramentas

Um LLM sozinho só escreve texto. Um **agente** é um LLM ligado a ferramentas: funções do sistema que ele pode pedir para executar. O modelo não executa nada; ele escreve um pedido estruturado, e o nosso código executa.

Exemplo do pedido que o modelo escreve quando decide reembolsar:

```json
{"name": "reembolsar", "arguments": {"id_pedido": "QTI-58213", "valor": 72.89, "motivo": "nao_entregue", "destino": "forma_original"}}
```

Analogia: um atendente que preenche um formulário, que o sistema depois processa. O risco que estudamos é o atendente preencher o formulário errado porque o cliente foi convincente.

#### Engenharia social

Manipular pessoas em vez de invadir sistemas. É a "lábia": convencer quem tem acesso a fazer o que não deveria. Com agentes de IA, o alvo deixa de ser o atendente humano e passa a ser o modelo.

#### Sandbox

Um ambiente de mentira e isolado, onde dá para errar sem consequência. Analogia: um simulador de voo. As empresas, os clientes, os CPFs e os valores são fictícios. O que é real é o comportamento do modelo lá dentro.

#### Verificador determinístico

"Determinístico" significa que a mesma entrada sempre dá a mesma saída. O verificador é um código que aplica as regras da política às ações do agente.

Analogia: a correção de uma prova de múltipla escolha (pelo gabarito) comparada à correção de uma redação (pela opinião de quem corrige). Um juiz LLM funciona como a correção de redação: é útil, mas varia.

Exemplo: a regra D2 do delivery escrita como lógica.

> Se a ação é `reembolsar`, com motivo `nao_entregue`, a entrega foi confirmada com o código e não existe protocolo válido autorizando, então houve **violação da D2**.

#### Professor, aluno e destilação

**Destilação** é usar um modelo grande (o professor) para gerar exemplos e treinar um modelo pequeno (o aluno) para imitá-lo. Analogia: o aprendiz que aprende observando o mestre trabalhar. O aluno fica menor, mais rápido e mais barato e, se os exemplos forem bons, aprende a parte do trabalho que importa para a tarefa.

#### Rejection sampling (amostragem por rejeição)

Gerar várias tentativas e ficar só com as aprovadas. Analogia: a peneira do garimpo. O professor nem sempre acerta; o verificador é a peneira, e só o que passa por ela vira exemplo de treino. A ideia aparece em vários trabalhos de pós-treino, como o STaR (Zelikman et al., 2022).

#### Destilação de contexto

O professor atende com uma "cola": o prompt reforçado, que tem um checklist contra manipulação. Na hora de salvar o exemplo de treino, tiramos a cola e guardamos só o prompt simples. O aluno aprende a agir como se tivesse a cola, sem precisar dela.

Analogia: o estudante que estuda com o resumo ao lado até não precisar mais dele. A vantagem prática é que o prompt do aluno fica menor, e cada chamada fica mais barata e mais rápida.

#### SFT (ajuste fino supervisionado)

Treinar um modelo já pronto com exemplos de "entrada → resposta certa". Analogia: aprender com exercícios resolvidos. No nosso caso, a entrada é a conversa até certo ponto, e a resposta certa é o que o agente fez a seguir numa conversa aprovada.

#### LoRA e QLoRA (prévia; o detalhe vem no dia do treino)

Um modelo de 4B tem 4 bilhões de parâmetros, e ajustar todos exige muita memória. O **LoRA** congela o modelo e treina só alguns milhões de parâmetros em "adaptadores" pequenos acoplados a ele. Analogia: em vez de reescrever o livro, colar post-its nas páginas.

O **QLoRA** faz o mesmo com o livro "comprimido": o modelo guardado com 4 bits por número em vez de 16. É isso que faz o treino caber numa GPU gratuita.

#### Divisão anti-vazamento e tática fora do treino

**Vazamento** é quando algo do teste aparece no treino, e o modelo acerta o teste porque decorou. Analogia: uma prova que repete as questões do simulado. A nota sobe, mas não mede aprendizado.

Por isso dividimos os dados por cenário e deixamos uma tática inteira fora do treino. Se o modelo resistir a um golpe que nunca viu, aprendeu o princípio, e não as frases.

#### Pares mínimos

Dois cenários quase iguais, que só mudam no detalhe que decide a resposta. Exemplo: dois clientes dizem "meu pedido não chegou, vou no Procon". No sistema de um, o entregador marcou o pedido como "extraviado" (ele tem direito ao reembolso). No do outro, a entrega foi confirmada com o código de entrega (não tem). A frase é a mesma e a resposta certa é oposta. É isso que impede o modelo de usar o tom como atalho.

#### Atalho (*shortcut learning*)

É quando o modelo aprende uma pista superficial que funciona nos dados de treino, mas não é o motivo real. Exemplo: se todo golpista do treino ameaçasse com o Procon e nenhum cliente honesto ameaçasse, o modelo aprenderia "Procon = golpe" e barraria o cliente honesto irritado. Geirhos et al. (2020) descrevem esse fenômeno em redes neurais em geral.

#### Linha de base (*baseline*)

O ponto de comparação. "O modelo ficou 30% melhor" não quer dizer nada se não diz **melhor do que o quê**. Uma linha de base fraca infla o resultado; uma forte o torna crível.

A nossa linha de base mais forte é o modelo pequeno sem ajuste, mas com o prompt reforçado. Se ele já resolvesse o problema, não precisaríamos treinar nada.

#### Fraude × atrito

O dilema central da prevenção a fraudes. Analogia: o porteiro de um prédio. Se ele deixa todo mundo entrar, nenhum morador é barrado, mas o ladrão passa. Se não deixa ninguém entrar, o ladrão não passa, mas os moradores ficam na rua. Os dois extremos são fáceis; o difícil é barrar o ladrão e deixar o morador entrar. Por isso medimos as duas taxas sempre juntas.

#### pass^k (consistência)

A chance de o agente acertar o mesmo cenário em **todas** as k tentativas. Exemplo: um agente que acerta 2 de 3 rodadas tem 67% de acerto médio (pass^1), mas o pass^3 dele naquele cenário é zero. Em produção, com milhares de atendimentos, o "às vezes erra" vira "erra todo dia". A métrica vem do τ-bench (Yao et al., 2024).

#### Intervalo de confiança e bootstrap

Um número medido em 100 cenários tem incerteza: com outros 100 cenários, ele sairia um pouco diferente. O **intervalo de confiança (IC) de 95%** é a faixa em que esperamos que o valor real esteja.

O **bootstrap** estima essa faixa sem fórmulas complicadas. Sorteamos, com reposição, uma "nova amostra" do mesmo tamanho a partir dos cenários que temos, recalculamos a métrica e repetimos isso 10.000 vezes. Os 95% do meio desses resultados formam o IC.

Exemplo: o modelo A tem taxa de fraude de 12%, com IC de 8% a 17%. O modelo B tem 30%, com IC de 24% a 36%. Os intervalos nem se encostam, então a diferença dificilmente é sorte. *(Números ilustrativos, não são resultados.)*

#### Bootstrap por cenário e bootstrap pareado

- **Por cenário:** as 3 rodadas de um mesmo cenário se parecem entre si. Se sorteássemos rodadas soltas, fingiríamos ter mais informação do que temos, e o IC sairia estreito demais. Por isso sorteamos cenários inteiros.
- **Pareado:** para comparar dois modelos, usamos os mesmos cenários sorteados para os dois em cada repetição. Assim a diferença não vem de "um pegou cenários mais fáceis que o outro".

#### Ablação

Tirar uma peça para ver se ela faz falta. Analogia: tirar o sal da receita para provar que o sal importa. Faremos duas: treinar sem o filtro do verificador (o verificador faz diferença?) e com metade dos dados (mais dados ajudariam?).

#### Pré-registro

Escrever a aposta antes do jogo. As hipóteses e os critérios de sucesso ficam commitados no git antes de qualquer dado existir. Isso impede, e prova que não aconteceu, a prática de testar várias métricas e mostrar só a que "deu certo", que em estatística se chama *p-hacking*.

#### Juiz LLM e kappa de Cohen

O juiz LLM classifica a causa raiz das falhas. Para saber se ele é confiável, você classifica 50 casos e comparamos com ele.

Só que concordar por acaso é fácil: se quase tudo é "cedeu à pressão", dois chutes já concordam muito. O **kappa de Cohen** mede a concordância **descontando a parte que aconteceria por acaso**. Zero significa concordância de acaso, e 1, concordância perfeita. Acima de 0,6 é considerado substancial.

#### Contrato de dados

O acordo sobre o formato dos arquivos que uma parte do sistema escreve e outra lê. Analogia: a tomada padrão. Quem fabrica o aparelho e quem constrói a parede não precisam conversar. É isso que permite construir o painel e o portfólio em paralelo ao motor.

#### Licença de modelo

O documento que diz o que você pode fazer com o modelo. **Apache 2.0** e **MIT** são permissivas: dá para usar, modificar e redistribuir, inclusive para fins comerciais, e para usar as saídas no treino de outro modelo. Licenças próprias ("other") podem trazer restrições de uso, de nome ou de receita.

Os modelos fechados (Claude, GPT, Gemini) têm termos de uso que costumam proibir usar as saídas para treinar modelos concorrentes. Por isso eles só aparecem aqui como modelos avaliados.

### Alternativas que descartamos

| Alternativa | Por que não |
|---|---|
| Juiz LLM como decisor principal | Varia entre execuções, custa a cada julgamento e pode ter viés; e a nossa política dá para escrever como código |
| Modelo fechado como professor | Os termos de uso costumam proibir usar as saídas para treinar outro modelo |
| O mesmo modelo simulando golpistas no treino e no teste | O aluno poderia decorar o estilo do atacante, e o teste sairia inflado |
| Clientes honestos sempre calmos | O modelo aprenderia "pressão = golpe", e o atrito explodiria com clientes honestos irritados |
| Qwen3.5-4B ou Gemma 4 como modelo base | São mais novos, mas a arquitetura deles (atenção linear, multimodal) não tem suporte verificado na T4, e o problema só apareceria na sexta |
| Deixar a promessa anterior fora do treino | Testaria uma tática nova e uma ferramenta nova ao mesmo tempo, e não daria para separar as causas |
| Medir a latência no seu notebook | Não representa um servidor, e ninguém conseguiria reproduzir |

### Perguntas de entrevista sobre esta etapa

**1. "Por que você usou um verificador determinístico em vez de um LLM como juiz?"**

> "Porque o rótulo é a base de tudo: ele decide o que entra no treino e o que conta como acerto na avaliação. Um juiz LLM erra, varia entre execuções e pode favorecer modelos parecidos com ele. Como a política do meu ambiente pode ser escrita como regras, eu a transformei em código: o verificador olha as ações que o agente executou e diz qual regra foi violada. É o mesmo princípio do τ-bench, que julga pelo estado final do banco de dados. O LLM só entra para classificar a causa raiz das falhas, e eu medi a concordância dele com a minha própria revisão."

**2. "Como você garante que o modelo não decorou o teste?"**

> "Com três camadas. A divisão é por cenário, e o conjunto de teste foi congelado antes do treino, com o hash registrado no git. Uma tática inteira, o fracionamento, ficou fora do treino, e um filtro removeu as conversas de treino em que ela aparecia por acidente. E o golpista simulado da avaliação é de outra família de modelos, então o modelo não pode ter decorado o estilo do atacante."

**3. "Como você evitou que o modelo aprendesse a negar tudo?"**

> "Medindo o atrito com o mesmo peso da fraude e usando pares mínimos: cada tática aparece também com clientes honestos. Um cliente que ameaça ir ao Procon e tem direito precisa ser atendido. Se o modelo usasse o tom como atalho, a taxa de atrito subiria. E eu defini, antes do experimento, que o atrito não podia subir mais de 5 pontos percentuais."

**4. "Por que treinar um modelo pequeno, se os modelos de ponta custam dez centavos de dólar por milhão de tokens?"**

> "Essa era uma das perguntas do projeto, e eu não presumi a resposta. Calculei o custo das APIs a partir dos tokens medidos e do preço de tabela, estimei o do modelo próprio a partir do preço de GPU por hora e da vazão medida, e mostrei a partir de qual volume o modelo próprio compensa. Além do custo, há motivos que não aparecem na conta: os dados do cliente não saem da empresa, o que importa para a LGPD, e eu não fico dependente de um fornecedor que pode mudar o modelo sem aviso."

**5. "Como você sabe que a diferença entre dois modelos não é sorte?"**

> "Cada cenário roda 3 vezes, e eu calculo intervalos de confiança de 95% por bootstrap, reamostrando cenários inteiros, porque rodadas do mesmo cenário não são independentes. Para comparar modelos, uso bootstrap pareado nos mesmos cenários. E as hipóteses principais foram escritas e commitadas antes de existir qualquer dado, então eu não escolhi a métrica depois de ver o resultado."

---

## Etapa 0, revisão: custo zero e foco no iFood (terça, 10/11/2026, noite)

### O que mudou

1. **O foco é o iFood.** O setor 2 deixou de ser um varejo genérico e virou um app fictício de delivery de comida, o Quati. A política anterior do varejo (Loja Tamanduá) não foi jogada fora: virou o setor 3, que só aparece na avaliação, para testar se o modelo aplica uma política que nunca viu.
2. **O orçamento é zero.** Pesquisamos o que existe de gratuito hoje e redesenhamos o plano: o professor e os simuladores rodam na GPU gratuita do Kaggle, com modelos abertos; as APIs gratuitas de terceiros só entram na avaliação.
3. **A identidade do git mudou.** Os commits desta pasta saem com o nome e o e-mail da conta nova. A configuração foi feita só neste repositório, então as outras pastas do computador continuam como estavam.

### Por que foi feito assim

**Delivery:** as ferramentas que o briefing previa para o varejo (consultar pedido, reembolsar, emitir cupom, cancelar, trocar endereço) são exatamente as de um app de delivery. Trocar o cenário não custa quase nada e coloca o projeto no domínio de quem vai avaliar a sua candidatura. Tomamos um cuidado: nada nas regras vem de informação interna de nenhuma empresa. São práticas públicas do setor, como o código de entrega e o cupom por atraso.

**Custo zero:** quando o dinheiro some, o recurso escasso passa a ser **tempo de GPU e cota de API**. O plano foi redimensionado para caber neles (menos conversas de treino, um teste um pouco menor), e a contabilidade dessas horas passa a ser publicada como resultado.

### Conceitos

#### Camada gratuita e limite de taxa

Muitas APIs têm uma **camada gratuita** (*free tier*): você usa sem pagar, mas com limites. Os limites aparecem com siglas:

- **RPM** (requisições por minuto);
- **RPD** (requisições por dia);
- **TPM** e **TPD** (tokens por minuto e por dia).

Analogia: uma torneira com vazão máxima (o RPM) ligada a uma caixa d'água que só enche uma vez por dia (o RPD).

Exemplo de conta: com 500 requisições por dia, e cada conversa usando cerca de 7 chamadas do agente, cabem umas 70 conversas por dia. É por isso que o Gemini roda só num subconjunto de cenários e começa já na quinta.

#### Rodar o modelo você mesmo × usar uma API

Usar uma **API** é pedir comida por delivery: você paga por prato e não se preocupa com a cozinha. **Rodar o modelo você mesmo** (*self-hosting*) é cozinhar em casa: os ingredientes são de graça (os pesos do modelo, com licença aberta), mas você precisa de fogão (a GPU) e de tempo.

Para nós, rodar o próprio modelo tem uma vantagem além do custo: a única regra que vale é a licença dos pesos (Apache 2.0). Não há termos de uso de um serviço dizendo o que você pode ou não fazer com as respostas.

#### Termos de uso de teste (*trial*)

O acesso gratuito da NVIDIA é um "teste": os termos permitem uso para "teste e avaliação internos, não produção". Usar as respostas para treinar um modelo que vamos publicar vai além disso. Então usamos a NVIDIA só para avaliar, e publicamos só as métricas dessas avaliações. **Ler os termos antes de usar um serviço gratuito** faz parte do trabalho de engenharia, e é uma boa história para contar numa entrevista.

#### MoE: por que um modelo de 30B roda rápido

Um modelo **MoE** (*Mixture of Experts*, mistura de especialistas) tem muitos "especialistas" internos, mas usa só alguns a cada token. O Qwen3-30B-A3B tem 30 bilhões de parâmetros no total e só 3 bilhões ativos por token. Analogia: um hospital com 30 especialistas, em que cada paciente é atendido por 3. O conhecimento é de um modelo grande e a velocidade é de um pequeno. É isso que torna viável usá-lo como professor numa GPU gratuita.

#### Quantização para servir o modelo (GGUF, Q4_K_M, MXFP4)

Para caber na memória da T4 (16 GB), o professor roda **quantizado**: os números do modelo são guardados com 4 bits em vez de 16. Analogia: uma foto em JPEG, que perde um pouco de detalhe e ocupa muito menos espaço. Os nomes estranhos são só os formatos: Q4_K_M e Q3_K_XL são formatos do llama.cpp, e MXFP4 é o formato de 4 bits em que o gpt-oss foi publicado.

#### llama.cpp como servidor

O llama.cpp roda modelos GGUF e expõe uma API no mesmo formato da OpenAI. Ele atende várias conversas ao mesmo tempo em "slots" paralelos. Analogia: um garçom atendendo várias mesas, em vez de esperar uma terminar para atender a próxima. Como a API tem o mesmo formato, o nosso harness conversa do mesmo jeito com o modelo no Kaggle, com a NVIDIA e com o Google.

#### Teste de fumaça

Um teste rápido e raso, só para ver se as peças funcionam juntas antes do trabalho de verdade. O nome vem da eletrônica: liga o aparelho e vê se sai fumaça. O nosso, na quarta, confere em uns 30 minutos se o modelo carrega, treina, chama ferramentas e é servido na GPU do Kaggle.

### Alternativas que descartamos

| Alternativa | Por que não |
|---|---|
| OpenRouter, modelos gratuitos | 50 requisições por dia sem crédito comprado; cada conversa usa umas 14 chamadas |
| Groq, camada gratuita | cerca de 200 mil tokens por dia por modelo: poucas conversas por dia |
| Cerebras | o plano gratuito acabou em julho de 2026; o teste atual pede cartão |
| GitHub Models | desativado em julho de 2026 |
| NVIDIA como fonte de dados de treino | os termos permitem só teste e avaliação; além disso, modelos já saíram do catálogo sem aviso |
| Pagar US$ 100 de API | sem orçamento, e o caminho gratuito ainda conta uma história melhor |

### Perguntas de entrevista sobre esta revisão

**1. "Você fez tudo isso sem gastar nada? Como?"**

> "Sim. O professor e os simuladores rodaram numa GPU gratuita do Kaggle, com modelos abertos e quantizados. O treino também foi no Kaggle. Para comparar com modelos de ponta, usei as camadas gratuitas do Google e da NVIDIA, só na avaliação. O recurso escasso passou a ser horas de GPU e cotas de API, então redimensionei o experimento para caber nelas e publiquei a contabilidade de cada etapa."

**2. "Por que o professor rodou na sua GPU, e não numa API gratuita?"**

> "Por causa da licença dos dados. O que entra no treino precisa vir de um modelo cuja licença permita treinar outro modelo com as saídas dele. Rodando um modelo Apache 2.0 por conta própria, a única regra que vale é a licença dos pesos. As APIs gratuitas que testei ou tinham limites pequenos demais, ou termos que permitem só teste e avaliação. Então elas ficaram só na avaliação."

**3. "Seu professor tem 30 bilhões de parâmetros. Isso não limita o aluno?"**

> "Limita o teto, e eu meço isso: o professor também é avaliado, como referência. Mas o filtro do verificador compensa uma parte, porque só entram no treino as conversas que estão certas pela política. Um professor menor aprova menos conversas, o que custa mais horas de GPU, mas não suja os dados. E o atacante da avaliação é de outra família, o que deixa o teste mais exigente, e não mais fácil."

**4. "O que o seu projeto tem a ver com o iFood?"**

> "Um dos setores do meu ambiente é um app de delivery fictício, com os casos do dia a dia: pedido que não chegou, item faltando, cupom por atraso, troca de endereço. Não usei nenhuma informação interna, só práticas públicas do setor. E a pergunta de custo é a mesma de uma empresa com muito volume: a partir de quantos atendimentos por mês vale a pena ter um modelo próprio?"

**5. "Você usou o Claude para construir o projeto. Por que não avaliou o Claude também?"**

> "Usei o Claude Code como par de programação, e digo isso no README. Não avaliei o Claude como agente por três motivos. Primeiro, a avaliação precisa da API da Anthropic, que é cobrada por uso, e o projeto tinha custo zero; a assinatura do Claude Code é para uso interativo, não para rodar milhares de conversas por código. Segundo, o Claude que me ajudou escreveu as políticas e os cenários, então ele seria um avaliado contaminado: é como o professor que escreveu a prova fazer a prova. Terceiro, os termos dos modelos fechados proíbem usar as respostas para treinar outro modelo, então ele também não poderia ser o professor. Deixei o harness pronto para quem tiver uma chave rodar a mesma avaliação."

### As 3 perguntas desta revisão, explicadas de outro jeito

Na primeira rodada, estas perguntas ficaram sem resposta. Aqui vai uma segunda explicação, por outro caminho.

#### 1. Por que a NVIDIA gratuita serve para avaliar, mas não para gerar dados de treino?

Pense num **test-drive**. A concessionária deixa você dirigir o carro para avaliar se ele é bom, mas não deixa você usar esse carro para trabalhar de motorista de aplicativo.

O acesso gratuito da NVIDIA é um test-drive. O contrato diz: "só para teste e avaliação internos, não para produção".

- **Avaliar o nosso modelo** é dirigir para testar. Pode.
- **Gerar dados de treino** é diferente: as respostas viram parte do nosso modelo, que vamos publicar. Isso é usar o carro para trabalhar. Não pode.

Há um segundo motivo, prático: a NVIDIA já tirou modelos do catálogo sem avisar. Se o professor sumisse no meio da geração, os dados ficariam pela metade.

> **Em uma frase de entrevista:** "Os termos gratuitos da NVIDIA permitem só teste e avaliação, então usei a NVIDIA para avaliar e gerei os dados de treino com modelos abertos rodando na minha própria GPU."

#### 2. O que é um MoE, e por que ele deixa um modelo de 30B rodar rápido?

Imagine uma **enciclopédia de 30 volumes**.

- Um modelo comum (chamado de "denso") consulta os 30 volumes para escrever **cada palavra**. É lento.
- Um modelo **MoE** tem um índice. Para cada palavra, o índice aponta só os 2 ou 3 volumes que interessam, e só esses são lidos.

O próprio nome do modelo traz os números. **Qwen3-30B-A3B** quer dizer 30 bilhões de parâmetros no total (os 30 volumes na estante) e 3 bilhões **a**tivos por palavra (o que ele de fato lê).

- **A velocidade** depende do que é lido. Ele trabalha como um modelo de 3B, com cerca de 10 vezes menos contas por palavra que um modelo denso de 30B. É rápido.
- **A memória** depende da estante inteira. Os 30B precisam ficar guardados, e por isso o modelo é comprimido (quantizado, como um arquivo zipado) para caber nas duas GPUs gratuitas de 16 GB.

**Por que isso importa para nós:** o professor precisa escrever milhares de conversas em poucas horas de GPU gratuita. Com um modelo denso do mesmo tamanho, não caberia no tempo.

#### 3. A conta do Gemini

Passo a passo:

1. Em cada conversa, o Gemini fala umas 7 vezes, e cada fala é 1 requisição. São **7 requisições por conversa**.
2. A cota é de 500 requisições por dia. 500 ÷ 7 ≈ 71, ou seja, **umas 70 conversas por dia**.
3. Cada cenário roda 3 vezes: 70 ÷ 3 ≈ **23 cenários por dia**.
4. De quinta a domingo são 4 dias: **no máximo uns 90 cenários**.

Os outros modelos rodam uns 200 cenários. O que isso muda no plano:

- o Gemini roda num **pedaço menor** do teste (60 a 90 cenários);
- com menos cenários, a incerteza é maior: o **intervalo de confiança dele fica mais largo**, e isso vai escrito ao lado do número;
- a cota **não acumula**: o dia não usado se perde, como um vale-refeição que vence no fim do dia. Por isso a avaliação do Gemini começa já na quinta.

---

## Etapa 1 — acesso ao Kaggle e teste de fumaça do ambiente (10/11/2026)

### O que foi feito

1. Conectamos a conta do Kaggle pelo cliente oficial (`kaggle auth login`), usando OAuth em vez de token colado em arquivo.
2. Escrevemos e rodamos, **em GPU real**, o notebook `notebooks/00-teste-de-fumaca/`, que mede o hardware que o Kaggle entrega e grava o resultado em `saida/ambiente.json`.

### Por que foi feito assim

**Por que OAuth e não o token da tela de configurações.** Os dois funcionam. O token é um segredo longo, sem prazo de validade, guardado em texto puro: se vazar, vale até alguém lembrar de expirá-lo à mão. O OAuth troca isso por duas credenciais com papéis separados — um *token de acesso*, que vence em 12 horas, e um *token de atualização*, que só serve para renovar o primeiro. A senha da conta não entra no fluxo, o escopo é explícito (`resources.admin:*`) e `kaggle auth revoke` cancela só este programa. Além da segurança, some a etapa manual de copiar e colar, e com ela o erro humano.

**Por que um teste de fumaça antes de qualquer treino.** O orçamento do projeto inteiro é a cota semanal de GPU do Kaggle (cerca de 30 horas) e o prazo é domingo. Descobrir uma incompatibilidade do ambiente no meio de um treino custa horas de cota e uma noite. O teste custou menos de dois minutos de GPU.

### O que o teste mediu (10/11/2026, `kind: measured`)

| | Medido |
|---|---|
| GPU | 2× Tesla T4, 14,6 GB de VRAM cada |
| Capacidade de cálculo | 7.5 (Turing) |
| CUDA / PyTorch | 13.0 / 2.11.0 |
| Python | 3.13.16 |
| CPU / RAM | 4 núcleos / 31 GB |
| Disco de trabalho | 20 GB |
| Instalados | transformers 5.20.2, accelerate 1.15.0, peft 0.21.2, datasets 4.8.5 |
| Ausentes | trl, bitsandbytes, vllm |

### Os três achados e o que eles mudam no plano

1. **O gargalo é o disco, não a VRAM.** São 20 GB no disco de trabalho, e o professor comprimido que queremos usar ocupa perto de 18 GB. O plano não previa esse limite. Consequência: o notebook do piloto precisa baixar o modelo direto para o disco temporário, ou usar uma quantização mais agressiva. Virou item de risco.
2. **A T4 não tem suporte nativo a bfloat16.** O bfloat16 exige capacidade de cálculo 8.0 (Ampere) para cima; a T4 é 7.5. O treino usa float16, que é mais sujeito a estouro numérico. Isso entra na configuração desde o início.
3. **Faltam `trl`, `bitsandbytes` e `vllm`.** A `trl` é a biblioteca que faz o ajuste fino. Instalação prevista no notebook de treino, com internet ligada.

### Qual dos três teria custado mais caro

O bfloat16 — não pelo tamanho, mas pelo **modo de falhar**. A falta de biblioteca quebra na primeira célula, com o nome do pacote no erro. O disco cheio quebra no download, com mensagem clara. Já o formato numérico errado pode deixar o treino rodar e produzir `NaN` depois de meia hora: o processo não para, só passa a aprender lixo, e você descobre na avaliação. A falha cara é a que não grita.

### Conceitos desta etapa

- **Teste de fumaça.** Verificação rápida e rasa feita antes do trabalho de verdade. Não prova que funciona; prova que não está obviamente quebrado. O nome vem da eletrônica: liga o circuito e vê se sai fumaça.
- **VRAM × RAM.** VRAM é a memória da placa de vídeo; RAM é a do computador. O modelo é carregado na RAM antes de ir para a VRAM, então RAM pequena trava o carregamento mesmo com VRAM sobrando.
- **VRAM não se soma.** Duas placas de 14,6 GB são dois espaços separados, e não um de 29 GB. Analogia: duas cozinhas em andares diferentes, com bancadas de 14,6 metros cada — não existe bancada de 29 metros.
- **Paralelismo de pipeline.** O jeito de usar as duas placas mesmo assim: as camadas 1 a 24 numa, as 25 a 48 na outra, e os dados atravessam na ordem. Permite rodar um modelo maior que uma placa, com duas ressalvas: nenhuma camada isolada pode passar de 14,6 GB, e as placas se revezam em vez de trabalharem em paralelo no mesmo dado.
- **bfloat16 × float16.** Dois formatos de 16 bits. O bfloat16 troca casas decimais por alcance, o que o torna mais resistente a estouro no treino, mas exige placas Ampere ou mais novas.

### Alternativas descartadas

| Alternativa | Por que não |
|---|---|
| Token de API colado em `~/.kaggle/access_token` | sem prazo de validade, em texto puro, com etapa manual de copiar e colar |
| `kaggle.json` (sistema legado) | formato antigo; o cliente atual o aceita só por compatibilidade |
| Pular o teste de fumaça e ir direto ao piloto | economizaria 2 minutos de GPU e arriscaria horas, com os três achados aparecendo durante o treino |
| Rodar o notebook à mão pelo site do Kaggle | não é reproduzível nem versionável; pelo cliente, o notebook mora no repositório e sobe por comando |

### Perguntas de entrevista sobre esta etapa

**1. Por que você usou OAuth em vez de uma chave de API no Kaggle?**
Porque a chave é um segredo permanente em texto puro, e o OAuth separa o token de acesso, que vence em 12 horas, do token de atualização, que só renova. Isso limita a janela de um vazamento, permite revogar só aquele programa sem trocar a senha e elimina a etapa manual de copiar e colar.

**2. Você tem duas GPUs de 14,6 GB. Dá para carregar um modelo de 25 GB?**
Não numa placa só, e a memória não se soma. Dá dividindo as camadas entre as duas, com paralelismo de pipeline. As restrições que a soma esconde são que nenhuma camada isolada pode passar de 14,6 GB e que as placas se revezam, então duas placas tornam o modelo possível, não duas vezes mais rápido.

**3. Por que gastar tempo com um teste de fumaça num projeto com prazo apertado?**
Justamente por causa do prazo. O orçamento é a cota de GPU, e uma incompatibilidade descoberta durante o treino custa horas de cota. O teste custou dois minutos e achou três problemas, um deles do tipo que falha silenciosamente.

**4. O que você faria diferente sabendo que a T4 não suporta bfloat16?**
Configuro o treino em float16 desde o início e vigio a perda em busca de `NaN`. Se aparecesse instabilidade, as saídas seriam reduzir a taxa de aprendizado, usar escalonamento de gradiente ou trocar de plataforma de GPU.

**5. Como você garante que a latência publicada no README significa alguma coisa?**
Porque o hardware medido é gravado junto, em `ambiente.json`, com `kind: measured`. Latência sem a máquina descrita ao lado não é comparável com nada.
