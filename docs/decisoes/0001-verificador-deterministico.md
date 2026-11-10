# ADR 0001: o verificador determinístico é o juiz principal

- **Status:** aceita em 10/11/2026
- **Data:** 10/11/2026

## Contexto

Precisamos de um "juiz" para duas tarefas:

1. decidir quais conversas geradas pelo professor **entram no treino**;
2. medir **fraude e atrito** na avaliação.

Se o juiz erra, o treino aprende o errado e a avaliação mede o errado, sem ninguém perceber. É a decisão mais importante do projeto.

## Opções consideradas

| Opção | Como funciona | A favor | Contra |
|---|---|---|---|
| A. Juiz LLM | Outro LLM lê a conversa e dá um veredito | Fácil de montar; entende nuances | Erra; varia entre execuções; custa a cada julgamento; pode favorecer modelos parecidos com ele. Zhang (2025), que usou juízes LLM, precisou de dois juízes e de recuperação manual quando o juiz devolveu respostas ilegíveis |
| B. Estado final esperado (como no τ-bench) | Compara o banco de dados no fim da conversa com um estado esperado escrito para cada cenário | Determinístico e barato | Precisa do estado esperado exato para cada cenário; não diz qual regra foi violada |
| **C. Política como código** | Registra cada ação do agente e confere uma a uma contra as regras da política, a partir do estado inicial. Também calcula a que o cliente tinha direito | Determinístico; explica qual regra e qual elo falhou; o mesmo código julga o Space ao vivo, onde não existe cenário pronto | Exige escrever a política como regras exatas; só enxerga o que virou ação |
| D. Revisão humana | Uma pessoa julga cada conversa | A mais confiável | Não escala para milhares de conversas |

## Decisão

**Opção C**, que inclui a B: o estado final é consequência das ações que o verificador confere.

As outras opções ficam em papéis de apoio:

- **D, revisão humana, audita o verificador:** você revisa veredictos sorteados.
- **A, o LLM, só classifica a causa raiz** das falhas, nunca o veredito. Medimos a concordância dele com você.

Na prática, o verificador é um conjunto de funções puras, uma por regra. Cada função recebe o estado inicial, a ação e as ações anteriores da conversa, e responde "permitida" ou "violou a regra X". O veredito da conversa sai dessas respostas e do direito do cliente.

## Consequências

**O que ganhamos**

- Rótulos reproduzíveis: julgar duas vezes dá o mesmo resultado.
- Custo zero por julgamento.
- Explicação de graça: "violou a D2, elo suficiência da verificação".
- Funciona ao vivo no Space: quem tentar aplicar um golpe vê na hora qual regra o agente quebrou.

**O que perdemos**

- A política precisa ser exata. Por isso as regras têm valores, prazos e listas fechadas. Casos que exigiriam julgamento subjetivo ("isso parece golpe?") foram evitados no desenho ou fixados pelo cenário.
- **Promessas feitas só em texto não aparecem.** Se o agente escreve "vou estornar" e não chama a ferramenta, o estado não muda e o verificador não vê nada. É exatamente o tipo de erro do caso da Air Canada. Mitigação: o juiz LLM marca, como métrica exploratória, conversas em que o agente prometeu algo fora da política. A solução completa fica no roadmap.
- Um bug no verificador contamina tudo. Por isso a validação abaixo é rígida.

## Como vamos validar

1. **Testes por regra**, com casos escritos à mão: para cada condição de cada regra, pelo menos um caso permitido e um proibido.
2. **Teste cruzado gerador × verificador:** para todo cenário gerado, o direito que o verificador calcula precisa bater com o rótulo do gerador. Se não bate, um dos dois está errado, e o teste falha.
3. **Testes de propriedade** (biblioteca Hypothesis): afirmações que precisam valer para qualquer entrada, como "se nenhuma ação de benefício foi executada, o veredito nunca é fraude".
4. **Auditoria humana:** antes da geração em escala, você revisa 30 veredictos sorteados, pelo menos 10 de cada tipo. Qualquer divergência para tudo até ser explicada.

## Referências

- Yao, S. et al. (2024). τ-bench. [arXiv 2406.12045](https://arxiv.org/abs/2406.12045): julgamento pelo estado final do banco.
- Zhang, J. (2025). [arXiv 2512.24415](https://arxiv.org/abs/2512.24415): exemplo de avaliação com juiz LLM e os cuidados que ela exige.
- Xu, Y. et al. (2026). Beyond Detection. [arXiv 2608.10239](https://arxiv.org/abs/2608.10239): os elos de confiança.
