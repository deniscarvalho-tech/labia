# Progresso: tudo o que foi feito, por categoria

> Arquivo de estudo e controle. Atualizado a cada etapa. Sai do repositório antes da candidatura (ver a última seção).

Legenda: **[pronto]** feito e testado · **[rodando]** em execução no Kaggle · **[pronto p/ rodar]** construído, esperando a vez · **[falta]** ainda não feito · **[você]** depende de você.

Última atualização: 11/11/2026, 20h30.

## 1. Pesquisa e rigor

| Item | Estado | Por que importa |
|---|---|---|
| Plano, políticas das empresas, taxonomia de táticas, cenários de exemplo (`docs/plano.md`, `docs/especificacao/`) | [pronto] | definem o que é golpe e o que é direito; sem isso não existe gabarito |
| Pré-registro das hipóteses H1, H2 e H3 (tag `pre-registro`, 10/11) | [pronto] | prova que as perguntas e a análise foram decididas antes dos dados; é o que separa pesquisa de "achar um número bonito" |
| Tática inteira fora do treino (pedido fatiado) | [pronto] | mede se o modelo aprendeu o princípio ou decorou exemplos |
| Pares mínimos (mesma tática em golpe e em cliente honesto) | [pronto] | impede o atalho "quem ameaça é golpista" |
| Teste congelado por hash (212 cenários) | [pronto] | ninguém consegue mexer no teste depois de ver o treino |
| Estatística: bootstrap por cenário, comparação pareada, Holm, pass^3, curva de resistência | [pronto] | todo número sai com intervalo de confiança; diferença pequena não vira "melhoria" |
| Raio-x da geração e gabaritos contestáveis (ADR 0008, tag `sensibilidade`) | [pronto] | achamos um defeito nosso e registramos a correção antes de ver resultados: é honestidade verificável |
| Defeito no laço: a última fala do cliente era descartada (ADR 0009) | [pronto] corrigido, com teste e trava na análise | a primeira avaliação do base media um artefato; foi refeita antes de qualquer resultado do modelo ajustado |
| Registro de decisões, ADRs 0001 a 0008 | [pronto] | cada escolha importante tem contexto, opções e motivo |

## 2. O motor (código)

| Item | Estado | Por que importa |
|---|---|---|
| Sandbox dos dois setores (Banco Saracura, Quati Delivery): 16 ferramentas, regras B1–B5, D1–D6, G1–G5 | [pronto] | é o "sistema interno" de mentira onde o agente age de verdade |
| Verificador determinístico | [pronto] | o juiz; julga ações, não texto, e por isso não é enganado por palavras |
| Gerador de cenários com semente fixa (2.010 de treino, 212 de teste) | [pronto] | reprodutível: rodar de novo dá exatamente os mesmos cenários |
| Laço de conversa, agora a classe `Conversation` | [pronto] | o mesmo código serve ao benchmark e à demo jogável |
| Cliente de LLM com cache, teto de chamadas e freio de ritmo | [pronto] | controle de custo e de limite das APIs gratuitas |
| Agentes roteirizados (ideal, crédulo, rígido, ruidoso) | [pronto] | testam o pipeline inteiro sem GPU |
| Filtro duplo (resultado certo + processo certo) | [pronto] | só entra no treino quem acertou pelo motivo certo |
| Módulo de treino SFT com LoRA (máscara só nas falas do agente, orçamento de tempo) | [pronto] | o treino em si |
| Contrato de dados (Pydantic → JSON Schema → TypeScript) | [pronto] | o painel e o Python nunca se desencontram |
| Relatório automático: hipóteses, sensibilidade, seção de resultados do README | [pronto] | nenhum número do README é digitado à mão |
| Model card e dataset card gerados dos resultados | [pronto] | a publicação no Hugging Face também sai de script |
| Custo estimado por mil conversas e ponto de equilíbrio GPU própria × API (`labia cost`) | [pronto] espera os resultados | responde "a partir de que volume vale treinar um modelo próprio?" |
| Gráficos do README, tema claro e escuro (`make charts`) | [pronto] espera os resultados | o relatório precisa de gráficos claros, gerados por script |

## 3. Engenharia e infraestrutura

| Item | Estado | Por que importa |
|---|---|---|
| uv + Makefile + Python 3.13, dependências travadas | [pronto] | reprodutível com um comando |
| 287 testes, lint (ruff) e tipagem estrita (mypy) | [pronto] | os testes pegaram bugs reais antes de gastar GPU |
| CI no GitHub: varredura de segredos (gitleaks) e testes em 3.11 e 3.13 | [pronto] | nenhuma chave vaza, e nada quebra sem aviso |
| Login do Kaggle por OAuth e renovação automática da credencial | [pronto] | o cliente do Kaggle tinha um defeito que derrubava a sessão a cada 12 h |
| Orquestrador e vigia das vagas de GPU (máximo de 2 no Kaggle) | [pronto] | encadeia as execuções sem ninguém acordar de madrugada |
| Script de publicação no Hugging Face (ensaio por padrão, recusa dado de exemplo) | [pronto] | publicar é um comando, e é impossível publicar exemplo por engano |

## 4. Execuções no Kaggle (GPU gratuita)

| Item | Estado | Resultado | Por que importa |
|---|---|---|---|
| 00. Teste de fumaça | [pronto] | 2× T4, sem bfloat16 | descobriu as limitações do hardware antes de planejar o treino |
| 01. Piloto do professor, versão 1 | [pronto, inválido] | cliente saía antes de ser atendido | o número "100% bloqueado" era falso; corrigido e guardado para registro |
| 01. Piloto do professor, versão 2 | [pronto] | gpt-oss-20b venceu: 274 aprovadas/h, 75% de aprovação | escolheu o professor por uma regra escrita antes |
| 02. Teste do treino | [pronto] | QLoRA cabe numa T4 (11,2 GB), mas a 154 tokens/s | mostrou que o treino precisava ser mais rápido |
| 03. Teste de velocidade | [pronto, falhou] | incompatibilidade de versões | virou uma sonda automática dentro do treino |
| 04. Geração do dado de treino (2 fatias) | [pronto] | 1.756 conversas aprovadas de 2.010 cenários, 8,5 h de GPU | é o dado de treino |
| 05. Avaliação do modelo-base, versão 1 | [pronto, inválido] | 85% das conversas com a última fala do cliente descartada | achou o defeito do laço (ADR 0009) |
| 05. Avaliação do modelo-base, versão 2 (laço corrigido) | [pronto] 4,6 h | fraude 16,9% e atrito 72,1% nas táticas vistas | a linha de base |
| 06. Treino SFT | [pronto] | Unsloth QLoRA numa GPU (as outras configurações estouraram a memória); 1,33 época em 4,2 h; perda de 1,48 para 0,35 | o modelo Lábia v0 (ADR 0010) |
| 06. Treino da ablação, sem o filtro | [pronto p/ rodar] com a configuração idêntica; espera vaga e cota | — | responde "o filtro do verificador faz diferença?" |
| 07. Avaliação do modelo ajustado | [pronto] 1,45 h | atrito caiu para 25,4% (H2 confirmada); fraude igual nas vistas (H1 não); fraude dobrou no pedido fatiado (H3 não, piorou) | o resultado principal da v0 |
| 07. Avaliação da ablação | [pronto p/ rodar] depois do treino dela | — | o efeito do filtro |
| 09. O modelo ajustado na CPU (latência da demo, 4 × 8 bits) | [pronto] só CPU (não gasta cota) | funciona de ponta a ponta; com o estado pré-aquecido, a 1ª resposta cai de 217 s para 12 s | garante que a demo ao vivo funciona e é usável |
| 08. Avaliação pelas APIs (DeepSeek, Gemini) | [pronto p/ rodar] [você] faltam as chaves | — | compara o modelo pequeno com modelos grandes |

## 5. Produto

| Item | Estado | Por que importa |
|---|---|---|
| Painel em React, 7 telas, modo escuro, tabela para cada gráfico | [pronto] com dados de exemplo | a demonstração visual dos resultados |
| Trava de publicação do painel (só publica dado real) | [pronto] | impossível publicar exemplo como se fosse resultado |
| Demo no Hugging Face: replay lado a lado e "Tente enganar o agente" | [pronto] testada com agente roteirizado | qualquer pessoa entende o problema em 30 segundos jogando |
| Publicar painel (GitHub Pages), modelo, dataset e demo | [falta] depois da avaliação | — |
| GIF da demo para o README | [falta] | — |

## 6. Documentação

| Item | Estado | Por que importa |
|---|---|---|
| README no formato de relatório técnico | [pronto] com resultados, gráficos, custo e análise de erros, tudo por script | a vitrine do projeto |
| `experiments/`: o resumo de cada execução | [pronto] | todo número publicado tem fonte |
| Como rodar, mapa do código | [pronto] | reprodutibilidade |
| Diário de aprendizados (etapas 1 a 7), glossário, explicação prática | [pronto] | estudo para a entrevista |
| Revisão do português do professor | [você] | último critério da escolha do professor |

## 7. Pendências que dependem de você

1. Revisar as 10 conversas em `docs/revisao/revisao-portugues-professor.md`.
2. Criar as chaves da NVIDIA e do Google AI Studio e anexá-las como Kaggle Secrets ao notebook `labia-08-avaliacao-api` (`docs/como-rodar.md`, seção 7).
3. Criar a conta e um token de escrita no Hugging Face, colocado no `.env` como `HF_TOKEN`.
4. Ligar o GitHub Pages: Settings → Pages → Source: GitHub Actions.
5. Apagar a pasta `C:\WINDOW~1` (criada por engano; tem só um arquivo de 2 bytes).
6. Opcional: trocar o nome de exibição no GitHub para "Denis Carvalho".

## Limpeza antes de publicar a candidatura (até 15/11)

Combinado: tirar do repositório público o que tem cara de material de estudo, deixando o README profissional.

**Sai:**

- `docs/aprendizados.md`, `docs/glossario.md`, `docs/explicacao-pratica.md` e este `docs/progresso.md`;
- `docs/revisao/`;
- o tom didático de `docs/mapa-do-codigo.md` e `docs/como-rodar.md`: viram um `docs/arquitetura.md` curto e um "como reproduzir" enxuto.

**Recomendo manter** (é o que impressiona um engenheiro sênior):

- `docs/decisoes/` (ADRs);
- `experiments/`;
- `docs/especificacao/` (políticas e taxonomia);
- `docs/plano.md` (o pré-registro), revisado para o tom profissional;
- os cards do Hugging Face.

**Atenção:** apagar um arquivo não apaga o histórico do git. Quem abrir commits antigos ainda vê o conteúdo. Duas saídas, a decidir na hora da limpeza:

- aceitar isso, porque quase ninguém lê o histórico;
- guardar o material de estudo num repositório privado (por exemplo, `labia-estudos`) e publicar o repositório principal com o histórico reescrito. Essa saída é irreversível e só se faz com o seu ok.
