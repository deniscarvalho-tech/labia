# ADR 0002: modelo base Qwen3-4B-Instruct-2507

- **Status:** aceita em 10/11/2026
- **Data:** 10/11/2026

## Contexto

O briefing pede um modelo aberto de até uns 4B de parâmetros, com chamada de ferramentas, bom português e licença permissiva, que caiba na GPU gratuita do Kaggle ou do Colab.

Restrições concretas:

- O Kaggle oferece uma P100 (16 GB) ou duas T4 (16 GB cada), com cota semanal de cerca de 30 horas, que varia. Confira o valor na sua conta.
- A **T4 não tem suporte nativo a bfloat16**, o formato numérico que quase todo modelo moderno usa no treino. Na T4, treinamos em float16, que tem menos margem contra estouro numérico.
- O modelo precisa funcionar nas três ferramentas do nosso pipeline: Unsloth/TRL (treino), vLLM (avaliação na GPU) e llama.cpp (versão GGUF para CPU). Uma incompatibilidade em qualquer uma delas para o projeto.

Os dados abaixo foram consultados em 10/11/2026 direto na API do Hugging Face: licença, número de parâmetros e arquitetura.

## Opções consideradas

| Modelo | Licença | Parâmetros | Arquitetura | Português | Risco na T4 | Veredito |
|---|---|---|---|---|---|---|
| **Qwen3-4B-Instruct-2507** | Apache 2.0 | 4,0 B | densa, só texto | a família Qwen3 anuncia 119 idiomas e dialetos | baixo | **escolhido** |
| Qwen3.5-4B | Apache 2.0 | 4,7 B | híbrida: 24 camadas de atenção linear e 8 de atenção completa, com visão | 201 idiomas e dialetos | alto: os kernels de atenção linear na T4 não foram verificados em treino nem no vLLM | roadmap |
| Granite-4.2-3B (IBM) | Apache 2.0 | 3,7 B | densa, só texto | na lista oficial de idiomas testados | baixo a médio: ecossistema menor | **plano B** |
| Gemma-4-E4B-it | Apache 2.0 | 8,0 B na memória (cerca de 4 B "efetivos") | multimodal (texto, imagem, áudio) | 35+ idiomas prontos; 140+ no pré-treino | médio: o dobro de memória, e a geração anterior (Gemma 3) teve problemas de estouro numérico em float16 | descartado |
| Ministral-3-3B-Instruct-2512 | Apache 2.0 | 3,9 B | multimodal (visão) | sim | médio | descartado |
| SmolLM3-3B | Apache 2.0 | 3,1 B | densa | um dos 6 idiomas | baixo | descartado: menor e mais antigo; a vantagem dele é ter os dados de treino abertos |
| Phi-4-mini-instruct | MIT | 3,8 B | densa | sim | baixo | descartado: mais antigo (fev. 2025), sem vantagem clara |
| Llama-3.2-3B-Instruct | Llama 3.2 Community | 3,2 B | densa | sim | baixo | **excluído pela licença**, que não é permissiva |
| LFM3-1.7B | LFM ("other") | 1,7 B | — | sim | — | **excluído pela licença** |

## Decisão

**Qwen3-4B-Instruct-2507.**

1. **Licença Apache 2.0:** permite uso comercial, modificação e redistribuição do modelo ajustado.
2. **Chamada de ferramentas nativa,** com template pronto no tokenizador.
3. **Português:** a família Qwen3 foi treinada com 119 idiomas e dialetos.
4. **Arquitetura densa e "comum":** é a mais testada em Unsloth, vLLM e llama.cpp, inclusive na T4. Com o prazo que temos, maturidade vale mais que novidade.
5. **Não é um modelo de raciocínio:** responde direto, sem uma etapa de "pensar em voz alta" antes. Isso reduz a latência e o custo por decisão, que são métricas nossas.
6. **4,0 B de parâmetros:** em 4 bits, o modelo ocupa em torno de 3 GB e sobra memória para conversas longas no treino.

## Consequências

**O que ganhamos:** o menor risco técnico do caminho crítico.

**O que perdemos:** o modelo é de agosto de 2025. Um avaliador pode perguntar "por que não o mais novo?". A resposta: escolhi pelo risco, testei o ambiente antes do treino, e repetir a receita no Qwen3.5-4B e no Granite-4.2-3B está no roadmap para mostrar que ela não depende de um modelo específico.

## Como vamos validar

**Teste de fumaça**, na quarta, no Kaggle, com uns 30 minutos de GPU:

1. carregar o modelo em 4 bits na T4;
2. rodar 20 passos de treino com Unsloth, sem erro e com a perda caindo;
3. gerar 10 chamadas de ferramenta válidas, a partir de pedidos em português;
4. servir o modelo com vLLM na T4 e responder a uma chamada no formato da API da OpenAI.

Se algum item falhar e não tiver correção rápida, repetimos o teste com o Granite-4.2-3B, o plano B.

## Referências

- Model cards no Hugging Face: [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B), [Granite-4.2-3B](https://huggingface.co/ibm-granite/granite-4.2-3b), [Gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it), [Ministral-3-3B](https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512), [SmolLM3-3B](https://huggingface.co/HuggingFaceTB/SmolLM3-3B), [Phi-4-mini-instruct](https://huggingface.co/microsoft/Phi-4-mini-instruct).
- Limites do Kaggle: relatos de terceiros ([gpuperhour](https://gpuperhour.com/blog/free-cloud-gpus-and-credits), [aimultiple](https://aimultiple.com/free-cloud-gpu)). A fonte oficial é o painel da sua conta.
