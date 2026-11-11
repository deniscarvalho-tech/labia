# ADR 0009: a última fala do cliente chega ao agente, e a avaliação do modelo-base roda de novo

- **Status:** aceita
- **Data:** 11/11/2026, antes de existir qualquer resultado do modelo ajustado

## Contexto

A primeira avaliação do modelo-base (`experiments/05-avaliacao-base-v1/resumo.json`) deu um número extremo: dos 318 clientes honestos, o modelo atendeu corretamente só 37 e barrou 241. Número extremo pede leitura antes de virar resultado. A leitura mostrou dois fenômenos misturados:

1. **Falha real do modelo.** O agente escreve "estou liberando agora" sem chamar a ferramenta; o cliente agradece e sai. O verificador acerta ao marcar atrito. É o mesmo padrão "anunciar sem executar" da geração: 80 dos 241 honestos negados.
2. **Defeito do laço de conversa.** O agente pergunta "Deseja que eu faça o estorno?", e o cliente simulado responde e se despede na mesma mensagem: "Confirma o aumento. Obrigado [FIM]". O laço encerrava ao ver o `[FIM]`, **sem entregar essa fala ao agente**. Na prática, quem pede confirmação nunca recebia o "sim".

Medido em todas as conversas: em **85%** da avaliação do modelo-base e em **62%** da geração do professor, a última fala do cliente nunca chegou ao agente. Muitas dessas falas são despedidas inofensivas ("valeu, obrigado"). Outras são confirmações, novos pedidos ou nova insistência que mereciam resposta.

O defeito vai nas duas direções:

- **infla o atrito:** a confirmação do cliente honesto é ignorada;
- **pode esconder fraude:** o golpista que diz "ok, faz o reembolso [FIM]" também nunca dava ao agente a chance de errar.

## Opções consideradas

1. **Manter o laço e comparar base e ajustado assim mesmo**, já que os dois sofreriam o mesmo defeito. É descartada. A comparação ficaria "justa" num laço que mede errado, e o defeito favorece um estilo de resposta: agir sem confirmar parece melhor do que confirmar antes. As taxas absolutas, que vão para o README, ficariam erradas.
2. **Proibir o simulador de se despedir com texto** (mudar só o prompt do cliente). É descartada: o modelo pode desobedecer, e o defeito continuaria possível.
3. **Entregar a última fala ao agente, deixar que ele aja e só então encerrar.** É a escolhida. Num chat real, se o cliente diz "sim, pode fazer" e fecha a janela, o atendente ainda executa.

## Decisão

- `Conversation.customer_says` (em `src/labia/conversation.py`):
  - uma fala com texto e `[FIM]` vai para o agente, que responde (com ferramentas, se quiser), e só então a conversa fecha;
  - um `[FIM]` sozinho continua encerrando na hora.
- O teste `test_goodbye_with_a_request_still_reaches_the_agent` reproduz o caso. Ele falha no laço antigo e passa no novo.
- **A avaliação do modelo-base roda de novo** com o laço corrigido (commit `c7a683c`). O modelo ajustado, a ablação e as APIs também são avaliados nesse commit.
- A primeira avaliação fica guardada como **inválida**, para registro, como o piloto 1 (`experiments/05-avaliacao-base-v1`).

## O que isso muda no que já foi feito

- **Dado de treino: não muda.** A geração também rodou com o laço antigo, mas só entraram conversas que o verificador aprovou: resultado certo pelo processo certo. Uma conversa aprovada é correta independentemente do defeito. O efeito foi outro: algumas conversas em que o professor pedia confirmação foram reprovadas sem necessidade, e o treino viu menos exemplos desse estilo.
- **Números do professor: inflados.** Os 29,6% de honestos barrados na primeira tentativa (`experiments/04-geracao/analise.json`) incluem o defeito. Eles continuam publicados, mas com essa ressalva, e não são uma medida limpa do professor.
- **Hipóteses: não mudam.** H1 a H3 e a análise de sensibilidade continuam as mesmas. A correção veio da leitura do modelo-base, antes de existir qualquer resultado do modelo ajustado.

## Consequências

- **Custo:** cerca de 4 horas de GPU para refazer a avaliação do modelo-base, numa cota semanal de 30 horas.
- **Ganho:** a medida de atrito passa a refletir o comportamento do modelo, não um artefato do laço.

## Como validar

Na nova avaliação do modelo-base, a última fala de toda conversa encerrada pelo cliente com texto precisa ter uma resposta do agente depois dela. Um script confere isso antes de qualquer análise.

## Referências

- Yao et al., *τ-bench* (2024): o usuário simulado sinaliza o fim com um marcador próprio, e o estado final do sistema é o que se compara. O mesmo cuidado vale aqui: o que importa é o que o agente fez até o fim da conversa.
