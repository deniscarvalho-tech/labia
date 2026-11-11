import { CartesianGrid, ErrorBar, LabelList, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import type { Bundle, Slice } from "../lib/data";
import { modelColor, modelLabel, row } from "../lib/data";
import { fmt } from "../lib/format";
import { SECTOR, SPLIT } from "../lib/labels";
import { Card, ChartOrTable, ChartTooltip, DataTable, Legend } from "../components/ui";

interface Point {
  id: string;
  label: string;
  x: number;
  y: number;
  xErr: [number, number];
  yErr: [number, number];
  xCi: [number, number] | null;
  yCi: [number, number] | null;
  n: number;
  color: string;
}

/** Modelos que nenhum outro supera nas duas métricas ao mesmo tempo (menor é melhor nas duas). */
function pareto(points: Point[]): Point[] {
  const frontier = points.filter(
    (p) => !points.some((q) => q !== p && q.x <= p.x && q.y <= p.y && (q.x < p.x || q.y < p.y)),
  );
  return frontier.sort((a, b) => a.x - b.x);
}

export function FraudFriction({ data, slice }: { data: Bundle; slice: Slice }) {
  const m = data.metrics;
  const points: Point[] = m.models.flatMap((model) => {
    const fraud = row(m, model.id, "fraud_rate", slice);
    const friction = row(m, model.id, "friction_rate", slice);
    if (!fraud || !friction) return [];
    const err = (v: number, ci: [number, number] | null): [number, number] => (ci ? [v - ci[0], ci[1] - v] : [0, 0]);
    return [{
      id: model.id,
      label: modelLabel(m, model.id).replace(/^Exemplo: /, ""),
      x: friction.value,
      y: fraud.value,
      xErr: err(friction.value, friction.ci95),
      yErr: err(fraud.value, fraud.ci95),
      xCi: friction.ci95,
      yCi: fraud.ci95,
      n: fraud.n_scenarios + friction.n_scenarios,
      color: modelColor(m, model.id),
    }];
  });
  const frontier = pareto(points);

  const table = (
    <DataTable
      caption="Fraude e atrito por modelo"
      rows={points}
      columns={[
        { header: "Modelo", cell: (p) => p.label },
        { header: "Fraude que passou", cell: (p) => fmt.pct(p.y), numeric: true },
        { header: "IC 95% da fraude", cell: (p) => (p.yCi ? `${fmt.pct(p.yCi[0])} a ${fmt.pct(p.yCi[1])}` : "—"), numeric: true },
        { header: "Atrito", cell: (p) => fmt.pct(p.x), numeric: true },
        { header: "IC 95% do atrito", cell: (p) => (p.xCi ? `${fmt.pct(p.xCi[0])} a ${fmt.pct(p.xCi[1])}` : "—"), numeric: true },
        { header: "Na fronteira", cell: (p) => (frontier.includes(p) ? "sim" : "não") },
      ]}
    />
  );

  return (
    <Card
      title="Fraude × atrito"
      subtitle={
        <>
          Cada ponto é um modelo; as barras são o intervalo de confiança de 95% (bootstrap por cenário). O canto inferior
          esquerdo é o melhor: pouca fraude e pouco cliente honesto barrado. A linha liga os modelos da fronteira de Pareto.{" "}
          <span className="text-ink-3">
            {SECTOR[slice.sector]} · {SPLIT[slice.split]}
          </span>
        </>
      }
    >
      <ChartOrTable
        table={table}
        chart={
          <div>
            <Legend items={points.map((p) => ({ label: p.label, color: p.color }))} />
            <div className="mt-3 h-[420px]">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 16, right: 120, bottom: 32, left: 8 }}>
                  <CartesianGrid vertical={false} />
                  <XAxis
                    type="number"
                    dataKey="x"
                    domain={[0, 1]}
                    tickFormatter={fmt.pct}
                    label={{ value: "Atrito: clientes honestos barrados", position: "bottom", offset: 12, fill: "var(--ink-2)", fontSize: 12 }}
                  />
                  <YAxis
                    type="number"
                    dataKey="y"
                    domain={[0, 1]}
                    tickFormatter={fmt.pct}
                    width={56}
                    label={{ value: "Fraude que passou", angle: -90, position: "insideLeft", fill: "var(--ink-2)", fontSize: 12 }}
                  />
                  <Tooltip
                    cursor={false}
                    content={({ payload }) => {
                      const p = payload?.[0]?.payload as Point | undefined;
                      if (!p?.id) return null;
                      return (
                        <ChartTooltip
                          title={p.label}
                          rows={[
                            { label: "Fraude que passou", value: `${fmt.pct(p.y)}`, color: p.color },
                            { label: "IC 95%", value: p.yCi ? `${fmt.pct(p.yCi[0])} a ${fmt.pct(p.yCi[1])}` : "—" },
                            { label: "Atrito", value: fmt.pct(p.x) },
                            { label: "IC 95%", value: p.xCi ? `${fmt.pct(p.xCi[0])} a ${fmt.pct(p.xCi[1])}` : "—" },
                          ]}
                        />
                      );
                    }}
                  />
                  <Scatter data={frontier} line={{ stroke: "var(--ink-3)", strokeWidth: 1.5 }} shape={() => <g />} isAnimationActive={false} />
                  {points.map((p) => (
                    <Scatter key={p.id} data={[p]} fill={p.color} isAnimationActive={false}
                      shape={(props: { cx?: number; cy?: number }) => (
                        <g>
                          <circle cx={props.cx} cy={props.cy} r={14} fill="transparent" />
                          <circle cx={props.cx} cy={props.cy} r={6} fill={p.color} stroke="var(--surface-1)" strokeWidth={2} />
                        </g>
                      )}
                    >
                      <ErrorBar dataKey="xErr" direction="x" width={6} stroke={p.color} strokeWidth={1.5} />
                      <ErrorBar dataKey="yErr" direction="y" width={6} stroke={p.color} strokeWidth={1.5} />
                      <LabelList dataKey="label" position="right" offset={12} fill="var(--ink-2)" fontSize={12} />
                    </Scatter>
                  ))}
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>
        }
      />
    </Card>
  );
}
