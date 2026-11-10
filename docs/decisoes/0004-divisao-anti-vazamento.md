# ADR 0004: divisão por cenário e fracionamento como tática fora do treino

- **Status:** aceita em 10/11/2026
- **Data:** 10/11/2026

## Contexto

O teste precisa medir se o modelo **generaliza**, ou seja, se acerta casos que nunca viu. Existe **vazamento** quando alguma informação do teste chega ao treino. Aí o modelo acerta o teste porque o decorou, e o número sai inflado sem ninguém perceber. É o erro mais comum e mais grave em projetos de ML.

## Decisão

### 1. A divisão é por cenário, e o teste é congelado

- Todas as rodadas de um cenário ficam do mesmo lado. Nunca uma rodada no treino e outra no teste.
- Os cenários de teste são gerados com sementes separadas das do treino.
- Antes do primeiro treino, o arquivo de cenários de teste é **congelado**: o hash dele fica registrado no git. Qualquer mudança no teste depois disso aparece.
- Uma parte dos cenários de treino vira **validação**, usada para decisões como o número de épocas. O teste só é usado na avaliação final.

### 2. Uma tática inteira fica fora do treino: o fracionamento (T5)

Comparação entre as candidatas:

| Tática | A favor de deixá-la de fora | Contra |
|---|---|---|
| T1 Autoridade | É comum | Os pares legítimos dela (segmento real) ensinam a consultar o segmento; tirá-los empobrece o treino |
| T2 Ameaça | É a mais "brasileira" | Parecida com a T3, então generalizar seria fácil demais e o teste diria pouco |
| T3 Urgência e emoção | — | Mesmo problema da T2 |
| T4 Promessa inventada | É a melhor história (o caso da United) | A ferramenta `consultar_protocolos` só aparece em cenários de promessa. Deixar a T4 de fora testaria duas coisas novas ao mesmo tempo (tática e ferramenta), e não daria para saber qual explica o resultado |
| **T5 Fracionamento** | É a família mais eficaz no benchmark de Zhang (2025); é estruturalmente diferente (uma soma ao longo da conversa, e não uma alegação); todas as ferramentas continuam aparecendo no treino, então testamos **só** a tática nova; tem nome em auditoria | É provavelmente a mais difícil, e H3 pode dar resultado negativo |

**Decisão: T5.** Se H3 der negativo, isso é um achado honesto e útil ("o modelo aprendeu a resistir a alegações e pressão, mas não a somar pedidos"), e aponta um próximo passo claro: dados de fracionamento.

Os pares legítimos da T5 (vários pedidos que, somados, cabem no limite) também ficam fora do treino.

### 3. Filtro de contaminação

LLMs misturam táticas sem querer. Uma conversa de treino com fracionamento acidental vazaria a tática. Por isso:

- **Detector determinístico:** dois ou mais pedidos de benefício na mesma conversa de treino → a conversa sai;
- **Etiquetador LLM:** lista as táticas presentes em cada conversa de treino → sai qualquer conversa com T5;
- publicamos quantas conversas cada filtro removeu.

### 4. Simuladores diferentes no treino e no teste

Detalhado no [ADR 0003](0003-professor-e-simuladores.md). O aluno não pode ter decorado o atacante.

### 5. DPO (v1.1) só com cenários de treino

Os pares de preferência do DPO saem de rodadas em cenários **de treino**. Usar rodadas do teste para gerar pares seria vazamento.

## Consequências

**O que ganhamos:** um número de teste confiável e uma escada de generalização bem definida (cenário novo → tática nova → setor novo → anexo falso).

**O que perdemos:** menos variedade no treino (a T5 inteira sai) e uma H3 mais difícil de confirmar.

## Como vamos validar

- Um teste automatizado confere que nenhum `scenario_id` aparece nos dois lados da divisão.
- O hash do arquivo de teste fica no commit anterior ao primeiro treino.
- O relatório publica a contagem de conversas removidas por contaminação.

## Referências

- Zhang, J. (2025). [arXiv 2512.24415](https://arxiv.org/abs/2512.24415): o *payload splitting* foi a família mais eficaz.
- Russinovich, M. et al. (2024). Crescendo. [arXiv 2404.01833](https://arxiv.org/abs/2404.01833).
- Gardner, M. et al. (2020). Contrast Sets. [arXiv 2004.02709](https://arxiv.org/abs/2004.02709).
