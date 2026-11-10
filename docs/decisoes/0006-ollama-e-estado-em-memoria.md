# ADR 0006: Ollama no lugar do llama.cpp compilado, e estado da sandbox em memória

- **Status:** aceita em 10/11/2026
- **Data:** 10/11/2026
- **Muda:** o plano (seção 3) previa llama.cpp no Kaggle e SQLite na sandbox.

## Contexto

Duas escolhas do plano esbarraram na implementação.

1. **Servir os modelos no Kaggle.** O llama.cpp não publica binário pronto com suporte a CUDA para Linux. Compilar no Kaggle levaria em torno de 15 minutos a cada sessão nova, e cada sessão consome cota de GPU, que é o orçamento do projeto.
2. **Guardar o estado da sandbox.** O plano previa um banco SQLite. Na implementação, o estado de um cenário é pequeno (um cliente, alguns pedidos ou transações, protocolos) e precisa ser copiado a cada conversa, guardado dentro do próprio cenário e reproduzido pelo verificador.

## Opções

| Tema | Opção | Prós | Contras |
|---|---|---|---|
| Servidor | llama.cpp compilado | controle total das opções | ~15 min de GPU por sessão para compilar |
| Servidor | **Ollama** | binário pronto com CUDA; mesmo motor (ggml); API no formato da OpenAI com ferramentas; modelos do plano já publicados com quantização de 4 bits | menos controle fino (algumas opções só por variável de ambiente) |
| Servidor | vLLM | o mais rápido em GPUs novas | suporte a Turing (T4) é limitado e a T4 não tem bfloat16 |
| Estado | SQLite | familiar; consultas em SQL | mapeamento objeto-tabela, cópia por arquivo, o cenário guardaria só uma referência |
| Estado | **Pydantic em memória** | validado na entrada; vira JSON dentro do cenário; cópia com uma linha; mesmo código para a sandbox e o verificador | não escala para milhões de registros (não precisa) |

## Decisão

- **Ollama** para servir professor, simuladores e os modelos avaliados no Kaggle. Licença MIT. Os modelos do plano estão publicados: `qwen3:30b-a3b-instruct-2507-q4_K_M` (19 GB), `gpt-oss:20b` (14 GB) e `ministral-3:14b-instruct-2512-q4_K_M` (9,1 GB), consultados em ollama.com em 10/11/2026.
- **Estado em memória com Pydantic**, serializado em JSON dentro de cada cenário.
- O resto do projeto não muda: o cliente de LLM fala o formato da OpenAI, então trocar o servidor é trocar uma URL.

## Consequências

**O que ganhamos:** nenhum minuto de GPU gasto compilando; o cenário é autossuficiente (o JSON tem tudo para reproduzir o veredito); a sandbox e o verificador compartilham o mesmo código de estado.

**O que perdemos:** algumas configurações do servidor (contexto, paralelismo) passam por variáveis de ambiente do Ollama em vez de parâmetros por chamada. Os modelos quantizados do Ollama são os da biblioteca dele; se for preciso um GGUF específico, o Ollama importa de um arquivo.

**Também nesta etapa:** o ambiente local passou a usar Python 3.13, igual ao do Kaggle (medido no teste de fumaça). O 3.11 continua sendo a versão mínima e é testado na CI.

## Referências

- Biblioteca de modelos do Ollama: ollama.com/library (consultada em 10/11/2026).
- Teste de fumaça do ambiente: `notebooks/00-teste-de-fumaca/saida/ambiente.json`.
