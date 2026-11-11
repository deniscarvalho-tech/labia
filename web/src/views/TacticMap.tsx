import { useState } from "react";
import type { Tactic } from "../contract/metrics";
import type { Bundle, Slice } from "../lib/data";
import { modelLabel, row } from "../lib/data";
import { fmt } from "../lib/format";
import { SECTOR, TACTIC } from "../lib/labels";
import { Card, ChartOrTable, DataTable } from "../components/ui";

const ORDER: Tactic[] = ["none", "authority", "institutional_threat", "urgency_emotion", "fake_prior_promise", "split_request"];
const STEPS = 7;

/** Escala sequencial de um tom só (azul), do claro ao escuro: mais escuro = mais fraude. */
function step(value: number): number {
  return Math.min(STEPS - 1, Math.floor(value * STEPS));
}

interface Cell {
  model: string;
  label: string;
  tactic: Tactic;
  value: number;
  ci: [number, number] | null;
  n: number;
}

export function TacticMap({ data, slice }: { data: Bundle; slice: Slice }) {
  const m = data.metrics;
  const all: Slice = { sector: slice.sector, split: "all_test" };
  const tactics = ORDER.filter((t) => m.rows.some((r) => r.tactic === t && r.metric === "fraud_rate"));
  const cells: Cell[] = m.models.flatMap((model) =>
    tactics.flatMap((t) => {
      const r = row(m, model.id, "fraud_rate", all, t);
      return r ? [{ model: model.id, label: modelLabel(m, model.id).replace(/^Exemplo: /, ""), tactic: t, value: r.value, ci: r.ci95, n: r.n_scenarios }] : [];
    }),
  );
  const [focus, setFocus] = useState<Cell | null>(null);
  const cell = (model: string, t: Tactic) => cells.find((c) => c.model === model && c.tactic === t);

  const grid = (
    <div>
      <div className="overflow-x-auto">
        <div
          className="grid min-w-[640px] gap-[2px]"
          style={{ gridTemplateColumns: `minmax(160px, 1.4fr) repeat(${tactics.length}, minmax(76px, 1fr))` }}
          role="grid"
          aria-label="Fraude que passou por modelo e tática"
        >
          <div />
          {tactics.map((t) => (
            <div key={t} role="columnheader" className="px-1 pb-2 text-center text-xs font-medium text-ink-2">
              {TACTIC[t]}
              {t === "split_request" ? <div className="text-[10px] font-normal text-ink-3">fora do treino</div> : null}
            </div>
          ))}
          {m.models.map((model) => (
            <div key={model.id} className="contents" role="row">
              <div role="rowheader" className="flex items-center pr-2 text-sm text-ink">
                {modelLabel(m, model.id).replace(/^Exemplo: /, "")}
              </div>
              {tactics.map((t) => {
                const c = cell(model.id, t);
                if (!c) return <div key={t} className="rounded bg-surface-2" role="gridcell" aria-label="sem dado" />;
                const s = step(c.value);
                return (
                  <button
                    key={t}
                    type="button"
                    role="gridcell"
                    onMouseEnter={() => setFocus(c)}
                    onFocus={() => setFocus(c)}
                    aria-label={`${c.label}, ${TACTIC[t]}: ${fmt.pct(c.value)} de fraude`}
                    className="flex h-12 items-center justify-center rounded text-sm font-medium transition-[filter] hover:brightness-110"
                    style={{ background: `var(--seq-${s})`, color: `var(--seq-text-${s})` }}
                  >
                    {fmt.pct(c.value)}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </div>
      <div className="mt-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs text-ink-3">
          <span>0%</span>
          <span className="flex">
            {Array.from({ length: STEPS }, (_, i) => (
              <span key={i} className="h-3 w-7 first:rounded-l last:rounded-r" style={{ background: `var(--seq-${i})` }} />
            ))}
          </span>
          <span>100% de fraude</span>
        </div>
        <p className="min-h-5 text-sm text-ink-2" aria-live="polite">
          {focus
            ? `${focus.label} · ${TACTIC[focus.tactic]}: ${fmt.pct(focus.value)} (${fmt.ci(focus.ci)}; ${focus.n} cenários)`
            : "Passe o mouse ou o foco do teclado numa célula para ver o intervalo de confiança."}
        </p>
      </div>
    </div>
  );

  return (
    <Card
      title="Mapa de táticas"
      subtitle={
        <>
          Fraude que passou em cada combinação de modelo e tática, em todo o teste. Mostra onde cada modelo é vulnerável: um
          modelo pode resistir à ameaça e ceder à urgência. <span className="text-ink-3">{SECTOR[slice.sector]}</span>
        </>
      }
    >
      <ChartOrTable
        chart={grid}
        table={
          <DataTable
            caption="Fraude por modelo e tática"
            rows={cells}
            columns={[
              { header: "Modelo", cell: (c) => c.label },
              { header: "Tática", cell: (c) => TACTIC[c.tactic] },
              { header: "Fraude que passou", cell: (c) => fmt.pct(c.value), numeric: true },
              { header: "IC 95%", cell: (c) => (c.ci ? `${fmt.pct(c.ci[0])} a ${fmt.pct(c.ci[1])}` : "—"), numeric: true },
              { header: "Cenários", cell: (c) => c.n, numeric: true },
            ]}
          />
        }
      />
    </Card>
  );
}
