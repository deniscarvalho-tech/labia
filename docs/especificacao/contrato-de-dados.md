# Contrato de dados (v1.0.0)

## Para que serve

O motor de ML (Frente A), o painel em React (Frente B) e a página de portfólio (Frente C) são construídos em paralelo, em sessões separadas. O contrato de dados é o **acordo sobre o formato dos arquivos** que o motor escreve e os outros dois leem. Pense numa tomada padrão: quem faz o aparelho e quem faz a parede não precisam conversar, só respeitar o padrão.

O painel e o portfólio **só leem** estes arquivos. Nenhum número é digitado à mão em lugar nenhum.

## Arquivos

| Arquivo | Quem escreve | Quem lê | O que tem |
|---|---|---|---|
| `results/summary.json` | script de avaliação | portfólio, painel | os 3 a 4 números de destaque |
| `results/metrics.json` | script de avaliação | painel | todas as métricas, por modelo, setor, tática e divisão, com IC |
| `results/replay.json` | script de avaliação | painel | uma seleção de conversas para o replay |
| `results/audit_findings.json` | script de auditoria | painel, relatório em PDF | os achados de auditoria |
| `site-data/versions.json` | script de release | portfólio | o resumo de cada versão (v0, v1.1, v1.2, v1.3) |

As conversas completas (milhares delas) vão para o dataset no Hugging Face. O `replay.json` traz só uma seleção, com exemplos de cada tipo de veredito por modelo e tática.

## Regras que valem para todos os arquivos

1. **Cabeçalho comum** em todo arquivo:

   ```json
   {
     "schema_version": "1.0.0",
     "is_sample": true,
     "generated_at": "2026-11-11T22:00:00-03:00",
     "git_sha": "0000000",
     "release": "v0"
   }
   ```

2. **`is_sample`**: `true` quando os dados são de exemplo. Nesse caso, o painel mostra um selo visível de "DADOS DE EXEMPLO", a página de portfólio mostra "em construção" (o briefing dela proíbe números de exemplo), e o script de publicação **se recusa** a publicar.
3. **Todo número tem um tipo** (`kind`): `measured` quando sai de uma execução, ou `estimated` quando é calculado a partir de premissas. Os números estimados levam as premissas junto. Como o projeto não paga nenhuma API, **todo custo é `estimated`**: o do modelo próprio sai do preço público de GPU por hora; o das APIs sai dos tokens medidos multiplicados pelo preço de tabela, com a fonte e a data.
4. **Taxas vão de 0 a 1** (o painel formata como %). Os intervalos de confiança vêm em `ci95: [inferior, superior]` e podem ser `null` quando não se aplicam.
5. **Chaves em inglês, textos de exibição em português.** O código e o contrato ficam em inglês, padrão de mercado e mais fácil para ferramentas. Tudo o que aparece na tela (rótulos, notas) vem em português.
6. **Versionamento:** `schema_version` segue versionamento semântico. Uma mudança que quebra quem lê sobe o primeiro número.
7. **Fonte da verdade:** modelos Pydantic em Python (`labia/contracts/`) geram os JSON Schemas (`schemas/*.schema.json`), que geram os tipos TypeScript do painel. A CI valida todo arquivo de resultado contra o schema. Se o motor mudar o formato sem atualizar o contrato, a CI quebra antes de o painel quebrar.

## Valores fechados (enums)

| Campo | Valores |
|---|---|
| `sector` | `bank`, `delivery`, `retail` (v1.2, o setor fora do treino), `all` |
| `tactic` | `none`, `authority`, `institutional_threat`, `urgency_emotion`, `fake_prior_promise`, `split_request`, `fake_proof`, `all` |
| `split` | `seen_tactics`, `heldout_tactic`, `heldout_sector`, `all_test` |
| `defense` | `standard`, `reinforced` |
| `verdict` | `fraud_blocked`, `fraud_passed`, `served_correctly`, `friction_denied`, `friction_escalated`, `overgrant` |
| `trust_link` | `actor_authority`, `asset_control`, `verification_sufficiency`, `transaction_path` |
| `root_cause` | `claim_accepted_without_check`, `checked_but_ignored`, `exception_misapplied`, `lost_cumulative_count`, `pressure_without_new_fact`, `third_party_asset`, `other` |
| `metric` | `fraud_rate`, `friction_rate`, `friction_denied_rate`, `friction_escalated_rate`, `overgrant_rate`, `pass3`, `valid_tool_call_rate`, `verified_before_acting_rate`, `value_at_risk_brl_per_1k`, `cost_per_1k_usd`, `latency_turn_p50_s`, `latency_turn_p95_s`, `latency_decision_p50_s` |
| `kind` | `measured`, `estimated` |

> Os exemplos abaixo usam **valores ilustrativos** (zeros e textos de exemplo). Por isso todos trazem `is_sample: true`.

## `results/summary.json`

Os números de destaque, já prontos para exibir. Cada um é um "cartão" que se descreve sozinho, e o portfólio só precisa renderizar.

```json
{
  "schema_version": "1.0.0",
  "is_sample": true,
  "generated_at": "2026-11-11T22:00:00-03:00",
  "git_sha": "0000000",
  "release": "v0",
  "headline": [
    {
      "id": "fraud_rate_sft_vs_base",
      "label": "Fraude que passou",
      "model_id": "sft",
      "value": 0.0,
      "unit": "ratio",
      "ci95": [0.0, 0.0],
      "kind": "measured",
      "comparison": {"model_id": "base", "label": "modelo base", "value": 0.0, "ci95": [0.0, 0.0]},
      "note": "Cenários de teste com táticas vistas no treino; 3 rodadas por cenário."
    },
    {
      "id": "cost_per_1k_sft",
      "label": "Custo por mil conversas",
      "model_id": "sft",
      "value": 0.0,
      "unit": "usd",
      "ci95": null,
      "kind": "estimated",
      "assumptions": "Preço de GPU por hora (fonte e data) dividido pelas conversas por hora medidas no benchmark.",
      "comparison": {"model_id": "deepseek", "label": "DeepSeek-V4.1-Flash (API; tokens medidos × preço de tabela)", "value": 0.0, "ci95": null}
    }
  ]
}
```

Cartões previstos: fraude (SFT × base), atrito (SFT × base), fraude na tática nunca vista (SFT × base) e custo por mil conversas (SFT × um modelo de ponta, ambos estimados e com as premissas visíveis).

## `results/metrics.json`

Formato "longo": uma linha por combinação de modelo, setor, tática, divisão e métrica. É o formato mais fácil para filtrar e montar gráficos.

```json
{
  "schema_version": "1.0.0",
  "is_sample": true,
  "generated_at": "2026-11-11T22:00:00-03:00",
  "git_sha": "0000000",
  "release": "v0",
  "models": [
    {
      "id": "sft",
      "label": "Lábia v0 (SFT)",
      "base_model": "Qwen/Qwen3-4B-Instruct-2507",
      "params_b": 4.0,
      "license": "apache-2.0",
      "access": "self_hosted",
      "defense": "standard"
    }
  ],
  "rows": [
    {
      "model_id": "sft",
      "sector": "all",
      "tactic": "all",
      "split": "seen_tactics",
      "metric": "fraud_rate",
      "value": 0.0,
      "ci95": [0.0, 0.0],
      "n_scenarios": 0,
      "n_runs": 0,
      "kind": "measured"
    }
  ],
  "curves": [
    {
      "model_id": "sft",
      "type": "resistance_by_turn",
      "split": "all_test",
      "points": [{"turn": 1, "value": 0.0, "ci95": [0.0, 0.0]}]
    }
  ]
}
```

## `results/replay.json`

As conversas que o painel mostra no replay, com o momento em que o agente cedeu destacado.

```json
{
  "schema_version": "1.0.0",
  "is_sample": true,
  "generated_at": "2026-11-11T22:00:00-03:00",
  "git_sha": "0000000",
  "release": "v0",
  "conversations": [
    {
      "id": "conv-base-delivery-D2-ameaca-golpe-0007-r1",
      "scenario_id": "delivery-D2-ameaca-golpe-0007",
      "model_id": "base",
      "defense": "standard",
      "run": 1,
      "sector": "delivery",
      "tactic": "institutional_threat",
      "legit": false,
      "verdict": "fraud_passed",
      "violated_rules": ["D2"],
      "trust_link": "verification_sufficiency",
      "concession_turn": 2,
      "root_cause": {
        "label": "pressure_without_new_fact",
        "source": "llm_judge",
        "judge_model": "Qwen3-30B-A3B-Instruct-2507 (exemplo)",
        "human_review": null
      },
      "value_at_risk_brl": 0.0,
      "highlight": {"turn": 2, "text": "Exemplo: o agente reembolsou logo depois da ameaça, sem nenhum fato novo."},
      "messages": [
        {"turn": 1, "role": "customer", "content": "Texto de exemplo."},
        {
          "turn": 1,
          "role": "agent",
          "content": "Texto de exemplo.",
          "tool_calls": [{"name": "consultar_pedido", "arguments": {"id_pedido": "QTI-00000"}, "valid": true}]
        },
        {"turn": 1, "role": "tool", "name": "consultar_pedido", "content": {"status": "entregue"}}
      ],
      "cost_usd": 0.0,
      "latency_s": 0.0
    }
  ]
}
```

## `results/audit_findings.json`

O relatório de auditoria em formato de dados: escopo, achados com severidade, evidências, causa raiz, recomendação e reteste. É a mesma estrutura de um relatório de auditoria interna.

```json
{
  "schema_version": "1.0.0",
  "is_sample": true,
  "generated_at": "2026-11-11T22:00:00-03:00",
  "git_sha": "0000000",
  "release": "v0",
  "scope": {
    "agents": ["base", "sft"],
    "sectors": ["bank", "delivery"],
    "tactics": ["none", "authority", "institutional_threat", "urgency_emotion", "fake_prior_promise", "split_request"],
    "n_conversations": 0
  },
  "findings": [
    {
      "id": "ACH-001",
      "title": "Exemplo: reembolso concedido sob ameaça mesmo com a entrega confirmada por código",
      "severity": "high",
      "rule_ids": ["D2"],
      "trust_link": "verification_sufficiency",
      "models_affected": ["base"],
      "frequency": {"value": 0.0, "ci95": [0.0, 0.0], "kind": "measured"},
      "value_at_risk_brl_per_1k": 0.0,
      "evidence": ["conv-base-delivery-D2-ameaca-golpe-0007-r1"],
      "root_cause": "Texto de exemplo.",
      "recommendation": "Texto de exemplo.",
      "retest": {"status": "not_retested", "version": null}
    }
  ]
}
```

A severidade é calculada por uma regra fixa (uma matriz de frequência × valor em risco), definida no código e documentada, e não escolhida a dedo.

## `site-data/versions.json`

A linha do tempo das versões, que a página de portfólio lê. É gerado pelo script de release, a partir dos mesmos resultados.

```json
{
  "schema_version": "1.0.0",
  "is_sample": true,
  "generated_at": "2026-11-11T22:00:00-03:00",
  "versions": [
    {
      "version": "v0",
      "date": "2026-11-14",
      "title": "SFT com destilação filtrada pelo verificador",
      "status": "released",
      "changes": ["Texto de exemplo."],
      "headline": [],
      "links": {
        "github_release": null,
        "hf_model": null,
        "hf_dataset": null,
        "space": null,
        "article": null,
        "panel": null
      }
    }
  ]
}
```

O campo `headline` de cada versão usa exatamente o mesmo formato de cartão do `summary.json`.

## Quando isso vira código

Depois do seu ok, no começo da quarta: os modelos Pydantic, os JSON Schemas, os arquivos de exemplo (com `is_sample: true`) e um teste que valida tudo. A partir daí, a Frente B pode começar o painel.
