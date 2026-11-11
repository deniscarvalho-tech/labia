import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Bundle, Slice } from "../lib/data";
import { modelColor, modelLabel } from "../lib/data";
import { fmt } from "../lib/format";
import { SPLIT } from "../lib/labels";
import { Card, ChartOrTable, ChartTooltip, DataTable, Legend } from "../components/ui";

type Datum = { turn: number } & Record<string, number | [number, number] | undefined>;

export function Resistance({ data, slice }: { data: Bundle; slice: Slice }) {
  const m = data.metrics;
  const split = slice.split === "heldout_sector" ? "all_test" : slice.split;
  const curves = m.curves.filter((c) => c.split === split);
  const turns = Math.max(0, ...curves.flatMap((c) => c.points.map((p) => p.turn)));
  const rows: Datum[] = Array.from({ length: turns + 1 }, (_, turn) => {
    const d: Datum = { turn };
    for (const c of curves) {
      const p = c.points.find((x) => x.turn === turn);
      if (!p) continue;
      d[c.model_id] = p.value;
      if (p.ci95) d[`${c.model_id}__ci`] = [p.ci95[0], p.ci95[1]];
    }
    return d;
  });
  const series = curves.map((c) => ({ id: c.model_id, label: modelLabel(m, c.model_id).replace(/^Exemplo: /, ""), color: modelColor(m, c.model_id) }));

  return (
    <Card
      title="Curva de resistência por turno"
      subtitle={
        <>
          Fração dos golpes que o agente ainda não tinha cedido até cada turno da conversa (estimador de Kaplan–Meier). Conversas
          que acabam antes, sem o agente ceder, contam até o turno em que acabaram. Uma curva que cai cedo é um agente que cede
          na primeira pressão. A faixa clara é o IC de 95%. <span className="text-ink-3">{SPLIT[split]} · todos os setores</span>
        </>
      }
    >
      <ChartOrTable
        chart={
          <div>
            <Legend items={series} shape="line" />
            <div className="mt-3 h-[380px]">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={rows} margin={{ top: 12, right: 24, bottom: 28, left: 8 }}>
                  <CartesianGrid vertical={false} />
                  <XAxis dataKey="turn" type="number" domain={[0, turns]} ticks={rows.map((r) => r.turn)}
                    label={{ value: "Turno da conversa", position: "bottom", offset: 10, fill: "var(--ink-2)", fontSize: 12 }} />
                  <YAxis domain={[0, 1]} tickFormatter={fmt.pct} width={56} />
                  <Tooltip
                    cursor={{ stroke: "var(--axis)", strokeWidth: 1 }}
                    content={({ label }) => {
                      const d = rows.find((r) => r.turn === label);
                      if (!d) return null;
                      return (
                        <ChartTooltip
                          title={`Até o turno ${label}`}
                          rows={series.map((s) => ({ label: s.label, value: typeof d[s.id] === "number" ? fmt.pct(d[s.id] as number) : "—", color: s.color }))}
                        />
                      );
                    }}
                  />
                  {series.map((s) => (
                    <Area key={`${s.id}-ci`} dataKey={`${s.id}__ci`} type="stepAfter" stroke="none" fill={s.color} fillOpacity={0.1}
                      isAnimationActive={false} activeDot={false} />
                  ))}
                  {series.map((s) => (
                    <Line key={s.id} dataKey={s.id} type="stepAfter" stroke={s.color} strokeWidth={2} dot={false}
                      activeDot={{ r: 4, stroke: "var(--surface-1)", strokeWidth: 2 }} isAnimationActive={false} />
                  ))}
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        }
        table={
          <DataTable
            caption="Curva de resistência por turno"
            rows={rows}
            columns={[
              { header: "Turno", cell: (r) => r.turn, numeric: true },
              ...series.map((s) => ({
                header: s.label,
                cell: (r: Datum) => (typeof r[s.id] === "number" ? fmt.pct(r[s.id] as number) : "—"),
                numeric: true,
              })),
            ]}
          />
        }
      />
    </Card>
  );
}
