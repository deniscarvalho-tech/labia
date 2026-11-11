# ADR 0008: gabaritos contestáveis na tática da promessa, e uma análise de sensibilidade definida antes dos resultados

- **Status:** aceita
- **Data:** 11/11/2026, antes de qualquer resultado da avaliação (a avaliação do modelo-base estava rodando e nenhum número dela tinha sido visto)

## Contexto

Depois da geração, li as conversas em que o professor (gpt-oss-20b) errou. A meta era descobrir se o erro era do professor ou do **gabarito**, que é o que o cenário diz que é o atendimento certo. Fonte dos números: `experiments/04-geracao/analise.json`, gerado por `labia generation-report`.

O professor quase não deixa golpe passar: 3,7% na primeira tentativa. Mas barra 29,6% dos clientes honestos, e a pior célula é a da **promessa legítima** (tática T4, lado honesto): ele acerta só 33% delas.

A tática T4 funciona assim: os fatos de base são os de um golpe, e o protocolo registrado no sistema muda a resposta. A regra G5 da política diz que **"uma promessa registrada e válida deve ser cumprida, mesmo que seja uma exceção a esta política"**. Lendo os erros, achei dois tipos.

1. **Erro do professor.** Na maior parte dos casos, o professor consulta o protocolo, confirma que ele vale e escreve "Estorno confirmado! Vamos processar agora mesmo", mas não chama a ferramenta. Pela heurística de texto, 86 dos 185 honestos negados na primeira tentativa caem nesse padrão ("anunciou sem executar"). O verificador acerta ao chamar isso de atrito.
2. **Defeito do gabarito (meu).** Em seis combinações, a promessa legítima foi montada sobre um fato de base que torna a ação prometida absurda:

| Situação | Variante de base | Por que o gabarito é contestável |
|---|---|---|
| B1, estorno de tarifa | `ja-estornada` | a tarifa já foi estornada: a ferramenta devolve erro, e estornar de novo é pagar duas vezes |
| B3, MED do Pix | `ja-contestado` | a transação já tem contestação aberta: a segunda é duplicata |
| B3, MED do Pix | `fora-do-prazo` | o prazo do MED é regra do Banco Central; atendimento não dispensa |
| B4, desbloqueio | `bloqueio-judicial` | nenhuma promessa de atendente derruba ordem judicial |
| D3, item faltante | `item-inexistente` | reembolsar um item que não estava no pedido |
| D5, cupom por atraso | `cupom-ja-emitido` | o cupom desse atraso já foi emitido: o segundo é compensação em dobro |

Pela letra da política, a G5 manda cumprir. Pelo bom senso, um atendente cuidadoso recusaria ou transferiria. Quando a política escrita e o bom senso discordam, o gabarito fica **contestável**, e eu não devo cobrar do modelo um comportamento que um humano razoável também questionaria.

## Opções consideradas

1. **Corrigir o gerador e regerar o teste.** É descartada: o teste está congelado por hash desde o pré-registro. Mexer nele depois de ver o dado de treino é exatamente o tipo de ajuste que o pré-registro existe para impedir.
2. **Tirar esses cenários da análise principal.** Também descartada, porque é uma mudança de protocolo feita depois do início do experimento.
3. **Manter a análise principal como pré-registrada e acrescentar uma análise de sensibilidade sem esses cenários, definida agora, antes de qualquer resultado.** É a escolhida.

## Decisão

- A regra fica no código: `CONTESTED_PROMISE_VARIANTS` e `is_contested()` em `src/labia/scenarios/model.py`.
- Um teste trava exatamente quais cenários do teste congelado ela marca. São 2 de 212, ambos honestos com promessa:
  - `bank-B3-med-pix-promessa-legitimo-163042`;
  - `delivery-D5-cupom-atraso-promessa-legitimo-800566`.
- `labia evaluate` calcula H1, H2 e H3 duas vezes:
  - no teste inteiro: é a **análise principal**, como pré-registrado;
  - sem esses 2 cenários: é a **análise de sensibilidade**.
- O README mostra as duas. Se as conclusões divergirem, vale a principal, e a divergência é discutida.
- O dado de treino **não** foi alterado. O treino já estava rodando, e o efeito é pequeno: só 9 dos 1.756 exemplos aprovados vêm dessas variantes.

## Previsão registrada antes dos resultados

O dado de treino tem só **64 exemplos** de "cumprir uma promessa válida" (3,6% do total). No outro lado da mesma tática, são 162 exemplos de "recusar uma promessa falsa". O professor errou tanto nos honestos com promessa que o filtro descartou a maioria deles.

**Prevejo que, no teste, o atrito do modelo ajustado nos honestos com promessa (T4) vai ser o pior entre as táticas e pode ficar acima do atrito do modelo-base nessa célula.** Isso não é uma hipótese formal, porque não entra na correção de Holm. É uma previsão registrada para a análise de erros: se acontecer, a explicação já estava escrita antes; se não acontecer, também conto.

## Consequências

- **Ganho:** os resultados vêm com um teste de robustez cuja regra foi escrita antes de qualquer número. E a análise de erros ganha um achado real sobre o professor: anunciar a ação sem executá-la.
- **Custo:**
  - na análise de sensibilidade, a H2 perde 2 cenários honestos (6 pares por modelo);
  - o gerador continua produzindo essas combinações até a v1.
- **Na v1:**
  - o gerador deixa de oferecer essas variantes no lado honesto da T4;
  - a política ganha uma frase explícita: "promessas não valem contra ordem judicial, prazo regulatório ou ação já realizada".

## Como validar

O teste `test_contested_scenarios_in_frozen_test_set` falha se o gerador mudar e os cenários marcados deixarem de ser exatamente esses dois. O commit desta decisão é anterior ao download de qualquer resultado da avaliação: dá para conferir pela data do commit e pela tag `sensibilidade`.

## Referências

- Nosek et al., *The preregistration revolution* (PNAS, 2018): a análise confirmatória é a definida antes; o que vier depois é exploratório e precisa ser rotulado assim.
- Yao et al., *τ-bench* (2024): também julga o agente comparando o estado final do sistema com um gabarito anotado. Nesse desenho, todo erro do gabarito vira erro de medida, e por isso vale a pena auditar o gabarito com as falhas do próprio modelo forte.
