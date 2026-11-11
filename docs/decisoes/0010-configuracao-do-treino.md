# ADR 0010: o treino roda com QLoRA e Unsloth numa GPU, escolhido por medição

- **Status:** aceita
- **Data:** 11/11/2026

## Contexto

- **O hardware:** o Kaggle dá duas T4 de 14,6 GB, sem bfloat16 (ver `experiments/ambiente-kaggle.json`).
- **O dado:** 1.756 conversas com mediana de 3.133 tokens e máximo de 5.647. São longas porque cada uma carrega a política e as ferramentas no prompt de sistema.
- **O que já se sabia:** o teste do treino (`experiments/02-teste-treino`) mostrou que o QLoRA comum cabe numa T4, mas a 154 tokens por segundo. Nesse ritmo, uma época levaria cerca de 10 horas.

## Opções consideradas

O notebook de treino roda 3 passos de cada configuração com as 16 conversas mais longas, que são o pior caso de memória, e fica com a mais rápida que não falhar. Fonte: `experiments/06-treino-sft/resumo.json`.

| Configuração | Resultado medido |
|---|---|
| LoRA em 16 bits, duas GPUs (paralelismo de dados) | memória esgotada |
| QLoRA, duas GPUs | memória esgotada |
| LoRA em 16 bits, uma GPU | memória esgotada |
| **QLoRA com Unsloth, uma GPU** | **304,8 tokens/s na sonda, pico de 4,8 GB** |

As três primeiras estouram nas conversas de 5,6 mil tokens. O paralelismo de dados não ajuda nisso, porque cada GPU guarda o modelo inteiro e as ativações da sua conversa. O Unsloth cabe com folga porque reescreve as partes mais pesadas da conta (atenção, perda) e guarda as ativações de um jeito mais econômico.

## Decisão

**QLoRA com Unsloth, numa GPU**, com:

- posto 16 e alfa 32, em todas as projeções lineares de atenção e MLP;
- taxa de aprendizado 2e-4, agenda cosseno, 3% de aquecimento;
- lote efetivo de 8 conversas (1 por passo, acumulando 8);
- contexto máximo de 6.144 tokens, sem descartar nenhuma conversa;
- **perda só nos tokens do assistente:** 427.624 dos 5.605.905, ou 7,6%. O modelo aprende a responder como atendente, e não a imitar o cliente ou o texto da política;
- **número de épocas pelo orçamento.** Na velocidade da sonda, 2 épocas não cabiam em 85% das 8 horas, então o notebook escolheu 1,33. O treino real foi mais rápido que a sonda (490 tokens/s) e terminou em 4,2 h.

**A ablação sem o filtro usa exatamente esta configuração e o mesmo número de épocas, sem sonda.** A única diferença entre os dois modelos precisa ser o dado.

## Consequências

- **Custo:**
  - a segunda GPU ficou parada durante o treino;
  - 1,33 época é menos do que as 2 planejadas. Se o modelo ficar devendo, uma segunda passada é o primeiro experimento da v1.
- **Ganho:** o treino coube numa sessão gratuita, com folga de memória, e a escolha não dependeu de palpite.
- **Risco medido:** a perda caiu de 1,48 no primeiro registro para cerca de 0,35 no último, sem sinal de instabilidade. Perda baixa não prova que o modelo ficou bom. Quem decide é a avaliação.

## Como validar

As hipóteses H1 a H3 no teste congelado. Se a fraude não cair, a explicação candidata é pouca passada pelos dados, e o experimento seguinte é treinar 2 épocas completas.

## Referências

- Hu et al., *LoRA: Low-Rank Adaptation of Large Language Models* (2021).
- Dettmers et al., *QLoRA: Efficient Finetuning of Quantized LLMs* (2023).
- Unsloth (github.com/unslothai/unsloth): núcleos otimizados para ajuste fino com LoRA e QLoRA.
