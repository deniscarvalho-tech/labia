---
title: Lábia
colorFrom: gray
colorTo: green
sdk: gradio
sdk_version: 6.31.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: Tente aplicar um golpe num agente de atendimento treinado para não cair
---

# Lábia: a demo

Um agente de atendimento com ferramentas (reembolsar, estornar, desbloquear) vira alvo de engenharia social. A Lábia treina um modelo pequeno e aberto (Qwen3-4B) para **consultar o sistema antes de agir** e mede duas coisas juntas: quanto golpe passa e quanto cliente honesto é barrado.

Esta demo tem duas abas.

- **Replay da avaliação:** o mesmo cenário lado a lado em dois modelos. Começa pelo modelo-base e o modelo ajustado, nos casos em que os dois discordam. Cada ação no sistema aparece como um bloco que abre e mostra a resposta do sistema.
- **Tente enganar o agente:** você recebe a missão de um cliente, golpista ou honesto, e conversa com o modelo ajustado. No fim, o mesmo verificador da avaliação dá o veredito. O modelo roda numa CPU gratuita, então cada resposta pode levar um minuto.

O veredito sai de um verificador determinístico, que aplica a política escrita como código às ações registradas, nunca ao texto. Empresas, clientes e dados são fictícios: os CPFs têm o dígito verificador errado de propósito.

Código, relatório técnico e decisões: [github.com/deniscarvalho-tech/labia](https://github.com/deniscarvalho-tech/labia).

## Rodar localmente

```bash
pip install -r requirements.txt gradio==6.31.0
LABIA_AGENT=scripted python app.py    # interface com um agente de regras fixas, sem baixar o modelo
python app.py                         # com o modelo de verdade (baixa o GGUF do Hugging Face)
```
