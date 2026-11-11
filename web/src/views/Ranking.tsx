import type { MetricName } from "../contract/metrics";
import type { Bundle, Slice } from "../lib/data";
import { modelColor, modelLabel, row } from "../lib/data";
import { fmt } from "../lib/format";
import { SECTOR, SPLIT } from "../lib/labels";
import { Card, DataTable, Swatch } from "../components/ui";

interface Line {
  id: string;
  label: string;
  color: string;
  defense: string;
  values: Partial<Record<MetricName, { value: number; ci: [number, number] | null }>>;
  scenarios: number;
}

const METRICS: MetricName[] = [
  "fraud_rate",
  "friction_rate",
  "pass3",
  "valid_tool_call_rate",
  "verified_before_acting_rate",
  "value_at_risk_brl_per_1k",
];

function Bar({ value, color }: { value: number; color: string }) {
  return (
    <span aria-hidden className="ml-2 inline-block h-2 w-16 rounded-full bg-surface-2 align-middle">
      <span className="block h-2 rounded-full" style={{ width: `${Math.max(2, value * 100)}%`, background: color }} />
    </span>
  );
}

export function Ranking({ data, slice }: { data: Bundle; slice: Slice }) {
  const m = data.metrics;
  const lines: Line[] = m.models.map((model) => {
    const values: Line["values"] = {};
    for (const metric of METRICS) {
      const r = row(m, model.id, metric, slice);
      if (r) values[metric] = { value: r.value, ci: r.ci95 };
    }
    return {
      id: model.id,
      label: modelLabel(m, model.id).replace(/^Exemplo: /, ""),
      color: modelColor(m, model.id),
      defense: model.defense === "reinforced" ? "reforçado" : "padrão",
      values,
      scenarios: row(m, model.id, "fraud_rate", slice)?.n_scenarios ?? 0,
    };
  });
  lines.sort((a, b) => (a.values.fraud_rate?.value ?? 1) - (b.values.fraud_rate?.value ?? 1));
  const pct = (l: Line, k: MetricName, bar = false) => {
    const v = l.values[k];
    if (!v) return "—";
    return (
      <span title={fmt.ci(v.ci)}>
        {fmt.pct(v.value)}
        {bar ? <Bar value={v.value} color={l.color} /> : null}
      </span>
    );
  };

  return (
    <Card
      title="Ranking dos modelos"
      subtitle={
        <>
          Ordenado pela fraude que passou (menor primeiro). O IC de cada taxa aparece ao passar o mouse; a mesma informação está na
          visão fraude × atrito. <span className="text-ink-3">{SECTOR[slice.sector]} · {SPLIT[slice.split]}</span>
        </>
      }
    >
      <DataTable
        caption="Ranking dos modelos"
        rows={lines}
        columns={[
          { header: "#", cell: (l) => lines.indexOf(l) + 1, numeric: true },
          {
            header: "Modelo",
            cell: (l) => (
              <span className="flex items-center gap-2">
                <Swatch color={l.color} />
                {l.label}
              </span>
            ),
          },
          { header: "Prompt", cell: (l) => l.defense },
          { header: "Fraude que passou", cell: (l) => pct(l, "fraud_rate", true), numeric: true },
          { header: "Atrito", cell: (l) => pct(l, "friction_rate", true), numeric: true },
          { header: "pass^3", cell: (l) => pct(l, "pass3"), numeric: true },
          { header: "Chamadas válidas", cell: (l) => pct(l, "valid_tool_call_rate"), numeric: true },
          { header: "Verificou antes de agir", cell: (l) => pct(l, "verified_before_acting_rate"), numeric: true },
          {
            header: "Valor em risco por mil conversas",
            cell: (l) => (l.values.value_at_risk_brl_per_1k ? fmt.brlCompact(l.values.value_at_risk_brl_per_1k.value) : "—"),
            numeric: true,
          },
          { header: "Cenários", cell: (l) => l.scenarios, numeric: true },
        ]}
      />
      <p className="mt-3 text-xs text-ink-3">
        pass^3: fração dos cenários em que o modelo acertou as 3 rodadas (τ-bench). Um agente que acerta 2 em 3 também erra em
        produção.
      </p>
    </Card>
  );
}
