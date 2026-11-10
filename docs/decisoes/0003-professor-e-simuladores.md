# ADR 0003: professor e simuladores na nossa GPU; APIs gratuitas só para avaliação

- **Status:** aceita em 10/11/2026
- **Data:** 10/11/2026 (revisão 2, depois da definição de orçamento zero)

## Contexto

Quatro papéis usam modelos maiores que o aluno:

| Papel | O que gera | O texto entra no treino? |
|---|---|---|
| Professor | as falas e as chamadas de ferramenta do agente | **sim** (é o que o aluno imita) |
| Simuladores do treino | as falas do golpista e do cliente honesto | **sim** (como entrada) |
| Simulador da avaliação | as falas do cliente na avaliação | não |
| Juiz da causa raiz | um rótulo por conversa que falhou | não |

Duas restrições mandam nesta decisão:

1. **Orçamento zero.** Nenhum serviço pago e nenhum cartão.
2. **Licença.** O que entra no treino precisa vir de um modelo cuja licença permita usar as saídas para treinar outro modelo. Isso vale para o professor **e para os simuladores do treino**, porque o texto deles também fica nos dados.

Pesquisei as opções gratuitas em 10/11/2026:

| Opção gratuita | O que oferece | Por que serve ou não serve para gerar dados de treino |
|---|---|---|
| OpenRouter, modelos `:free` | 20 requisições por minuto e **50 por dia** sem crédito comprado | Não serve: cada conversa usa umas 14 chamadas |
| Groq | teto de cerca de 200 mil tokens por dia por modelo | Não serve: dá umas poucas conversas por dia |
| Cerebras | o plano gratuito acabou em julho de 2026; o teste atual pede cartão | Não serve |
| GitHub Models | desativado em julho de 2026 | Não existe mais |
| NVIDIA (build.nvidia.com) | cerca de 40 requisições por minuto, sem cartão, com dezenas de modelos abertos | **Não serve para treino:** os termos permitem só "teste e avaliação internos, não produção", e restringem o uso das saídas para criar produtos concorrentes. Além disso, modelos saíram do catálogo sem aviso em agosto de 2026. **Serve para avaliação** |
| Google AI Studio | camada gratuita do Gemini, com cota diária por projeto (cerca de 500 requisições por dia no Flash-Lite, segundo relatos de terceiros) | Para avaliação, sim. Para treino, não: modelo fechado |
| **Rodar o modelo nós mesmos no Kaggle** | GPU gratuita (2× T4, cerca de 30 h por semana) e modelos abertos | **Serve:** a licença dos pesos (Apache 2.0) é a única que vale. Custa horas de GPU |

## Decisão

### 1. O professor e os simuladores do treino rodam na nossa GPU

Dois candidatos, ambos Apache 2.0 e com versões quantizadas prontas (GGUF) que rodam com llama.cpp na T4:

| Candidato | Arquitetura | Memória aproximada | A favor | Contra |
|---|---|---|---|---|
| **Qwen3-30B-A3B-Instruct-2507** | MoE: 30 B de parâmetros no total, 3 B ativos por token | ~14 a 18 GB em 4 bits; divide-se entre as duas T4, ou cabe numa só em 3 bits | rápido (poucos parâmetros ativos); bom em ferramentas e em português; não é modelo de raciocínio | mesma família do aluno (o que pode até facilitar a imitação) |
| **gpt-oss-20b** | MoE: 21 B no total, 3,6 B ativos | ~12 GB (MXFP4); cabe numa T4 | treinado com hierarquia de instruções, então pode resistir melhor à manipulação | modelo de raciocínio: gera mais tokens por resposta; pode recusar o papel de golpista quando for simulador |

O mesmo modelo faz o papel de professor e o de simulador do treino, com prompts diferentes. Assim só um modelo ocupa a memória da GPU.

**Regra de escolha no piloto de quarta:** os dois atendem os mesmos ~20 cenários. Vence o que gerar **mais conversas aprovadas por hora de GPU**:

> conversas aprovadas por hora = conversas por hora × taxa de aprovação pelo verificador

Duas condições eliminam um candidato: menos de 95% de chamadas de ferramenta válidas, ou reprovação na sua revisão de 10 conversas (o português precisa soar natural). É a versão "custo zero" da regra anterior: em vez de dólares, otimizamos horas de GPU.

### 2. Destilação de contexto

O professor atende com o **prompt reforçado**: a política mais um checklist contra manipulação. Nos dados de treino, a mesma conversa é salva com o **prompt padrão**. O aluno aprende a agir como se tivesse o reforço, sem pagar os tokens dele a cada chamada.

Cuidado necessário: se o professor citar o checklist ("conforme o meu checklist..."), o aluno aprenderia a mencionar algo que não existe no prompt dele. Um filtro remove essas conversas.

### 3. O simulador da avaliação é de outra família, também na nossa GPU

**Ministral-3-14B-Instruct-2512** (Mistral AI, Apache 2.0, GGUF oficial de cerca de 8 GB em 4 bits). Ele vem de uma família diferente da do aluno e da dos dois candidatos a professor, então o aluno não pode ter decorado o estilo dele.

Rodar o simulador da avaliação na nossa GPU, e não numa API, tem mais uma vantagem: ele não some do catálogo no meio da semana. **Todas as configurações são avaliadas contra o mesmo simulador,** inclusive os modelos de ponta. Sem isso, a comparação não seria justa.

Se o Ministral recusar o papel de golpista com frequência (mais de 10% no piloto), o plano B é o gpt-oss-20b, desde que ele não seja o professor.

### 4. As APIs gratuitas entram só na avaliação, como linhas de comparação

| Linha de comparação | Serviço | Uso |
|---|---|---|
| DeepSeek-V4.1-Flash (aberto, de fronteira) | teste gratuito da NVIDIA | avaliação, com prompt padrão e com prompt reforçado |
| Gemini Flash-Lite (fechado) | camada gratuita do Google AI Studio | avaliação num subconjunto de cenários, por causa da cota diária |

**Regra de publicação:** dessas APIs publicamos as **métricas**. As conversas completas não vão para o dataset no Hugging Face, que só contém o que nós geramos com modelos abertos. Se um desses modelos sair do catálogo, a linha é trocada por outro modelo e a troca fica registrada no README.

**Claude e GPT ficam de fora:** não têm acesso gratuito. O harness aceita qualquer API no formato da OpenAI, então quem tiver uma chave paga pode rodar a mesma avaliação. Isso vai escrito no README.

### 5. Juiz da causa raiz

O próprio modelo do professor, rodando na nossa GPU. Os rótulos dele só valem no relatório se a concordância com a sua revisão de 50 casos for boa (kappa ≥ 0,6). Detalhes no [ADR 0005](0005-metricas-e-estatistica.md).

## Consequências

**O que ganhamos**

- Custo zero em dinheiro.
- Dados de treino limpos do ponto de vista de licença, documentados no README e no dataset card.
- Um simulador de avaliação estável, igual para todas as configurações.
- Uma história forte para entrevista: "treinei e avaliei um LLM com US$ 0, e mostro a conta das horas de GPU".

**O que perdemos**

- O professor fica menor (30 B ou 20 B, contra os modelos de fronteira que usaríamos pagando). A taxa de aprovação deve ser menor, o que custa mais horas de GPU. O verificador compensa a qualidade: só entra o que está certo.
- O simulador do treino também é menor, então o atacante do treino é mais fraco que o da avaliação. Isso deixa o teste mais difícil, e não mais fácil: é uma escolha conservadora.
- A comparação de ponta fica mais estreita: sem Claude e GPT, e com o Gemini num subconjunto menor.
- As horas de GPU do Kaggle viram o recurso escasso, e precisam de contabilidade diária.

## Como vamos validar

O piloto mede e mostra a você, antes de escalar:

- a taxa de aprovação de cada candidato a professor;
- as conversas por hora e as conversas aprovadas por hora;
- o percentual de chamadas de ferramenta válidas;
- o percentual de vezes em que cada simulador saiu do personagem ou recusou o papel (o limite é 10%);
- a sua revisão de 10 conversas.

## Referências

- Askell, A. et al. (2021). [arXiv 2112.00861](https://arxiv.org/abs/2112.00861): destilação de contexto.
- Snell, C. et al. (2022). Learning by Distilling Context. [arXiv 2209.15189](https://arxiv.org/abs/2209.15189).
- Zelikman, E. et al. (2022). STaR. [arXiv 2203.14465](https://arxiv.org/abs/2203.14465): gerar várias respostas e treinar só nas corretas.
- Nakash, I. et al. (2025). CRAFT. [arXiv 2506.09600](https://arxiv.org/abs/2506.09600): o atacante que lê a política.
- Model cards: [Qwen3-30B-A3B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507) ([GGUF](https://huggingface.co/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF)), [gpt-oss-20b](https://huggingface.co/openai/gpt-oss-20b) ([GGUF](https://huggingface.co/ggml-org/gpt-oss-20b-GGUF)), [Ministral-3-14B-Instruct-2512](https://huggingface.co/mistralai/Ministral-3-14B-Instruct-2512) ([GGUF](https://huggingface.co/mistralai/Ministral-3-14B-Instruct-2512-GGUF)).
- Limites gratuitos: [OpenRouter](https://openrouter.ai/docs/api-reference/limits); termos do teste da NVIDIA, citados em [DEV Community](https://dev.to/rudratosh/nvidia-will-run-glm-53-and-kimi-k3-for-you-for-free-i-read-the-fine-print-here-are-the-three-3mkj); [Google AI Studio](https://aistudio.google.com/docs/rate-limits).
