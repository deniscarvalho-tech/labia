import { useState, type ReactNode } from "react";
import type { Verdict } from "../contract/replay";
import type { Severity } from "../contract/audit_findings";
import { SEVERITY, VERDICT } from "../lib/labels";

export function Card({ title, subtitle, children, actions }: {
  title: string;
  subtitle?: ReactNode;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <section className="rounded-xl bg-surface p-5 shadow-[0_0_0_1px_var(--ring)]">
      <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-ink">{title}</h2>
          {subtitle ? <p className="mt-1 max-w-3xl text-sm text-ink-2">{subtitle}</p> : null}
        </div>
        {actions}
      </header>
      {children}
    </section>
  );
}

/** Selo visível de dados de exemplo: exigido pelo briefing enquanto não há resultado real. */
export function SampleBanner() {
  return (
    <div role="alert" className="border-b-4 border-[var(--status-warning)] bg-surface-2 px-4 py-3 text-sm">
      <div className="mx-auto flex max-w-6xl items-start gap-3">
        <span aria-hidden className="mt-0.5 inline-flex h-5 shrink-0 items-center rounded bg-[var(--status-warning)] px-2 text-xs font-bold text-[#0b0b0b]">
          DADOS DE EXEMPLO
        </span>
        <p className="text-ink-2">
          Os números desta página vêm de <strong className="text-ink">agentes roteirizados</strong> rodando no pipeline de
          verdade, não de modelos. Servem para mostrar o painel funcionando. Os resultados reais substituem estes arquivos
          quando a avaliação terminar, e o selo some sozinho.
        </p>
      </div>
    </div>
  );
}

export function KindBadge({ kind }: { kind: string }) {
  const estimated = kind === "estimated";
  return (
    <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs text-ink-2 shadow-[0_0_0_1px_var(--ring)]">
      {estimated ? "estimado" : "medido"}
    </span>
  );
}

const VERDICT_TONE: Record<Verdict, "good" | "warning" | "serious" | "critical"> = {
  fraud_blocked: "good",
  served_correctly: "good",
  friction_denied: "warning",
  friction_escalated: "warning",
  overgrant: "serious",
  fraud_passed: "critical",
};

const SEVERITY_TONE: Record<Severity, "good" | "warning" | "serious" | "critical"> = {
  low: "good",
  medium: "warning",
  high: "serious",
  critical: "critical",
};

function StatusIcon({ tone }: { tone: "good" | "warning" | "serious" | "critical" }) {
  const color = `var(--status-${tone})`;
  if (tone === "good") {
    return (
      <svg aria-hidden width="14" height="14" viewBox="0 0 16 16">
        <circle cx="8" cy="8" r="7" fill={color} />
        <path d="M4.5 8.2l2.2 2.2 4.8-4.8" stroke="#fff" strokeWidth="1.8" fill="none" strokeLinecap="round" />
      </svg>
    );
  }
  if (tone === "critical") {
    return (
      <svg aria-hidden width="14" height="14" viewBox="0 0 16 16">
        <circle cx="8" cy="8" r="7" fill={color} />
        <path d="M5.5 5.5l5 5M10.5 5.5l-5 5" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg aria-hidden width="14" height="14" viewBox="0 0 16 16">
      <path d="M8 1.5L15 14H1z" fill={color} />
      <path d="M8 6v3.6" stroke={tone === "warning" ? "#0b0b0b" : "#fff"} strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="8" cy="11.8" r="1" fill={tone === "warning" ? "#0b0b0b" : "#fff"} />
    </svg>
  );
}

/** Status sempre com ícone e texto: a cor nunca carrega o significado sozinha. */
export function VerdictPill({ verdict }: { verdict: Verdict }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-surface-2 px-2.5 py-1 text-xs font-medium text-ink">
      <StatusIcon tone={VERDICT_TONE[verdict]} />
      {VERDICT[verdict]}
    </span>
  );
}

export function SeverityPill({ severity }: { severity: Severity }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-surface-2 px-2.5 py-1 text-xs font-medium text-ink">
      <StatusIcon tone={SEVERITY_TONE[severity]} />
      Severidade {SEVERITY[severity].toLowerCase()}
    </span>
  );
}

export function Swatch({ color, shape = "dot" }: { color: string; shape?: "dot" | "line" }) {
  return shape === "line" ? (
    <span aria-hidden className="inline-block h-0.5 w-4 rounded" style={{ background: color }} />
  ) : (
    <span aria-hidden className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: color }} />
  );
}

export function Legend({ items, shape = "dot" }: { items: { label: string; color: string }[]; shape?: "dot" | "line" }) {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">
      {items.map((i) => (
        <li key={i.label} className="flex items-center gap-1.5">
          <Swatch color={i.color} shape={shape} />
          {i.label}
        </li>
      ))}
    </ul>
  );
}

export interface Column<T> {
  header: string;
  cell: (row: T) => ReactNode;
  numeric?: boolean;
}

export function DataTable<T>({ rows, columns, caption }: { rows: T[]; columns: Column<T>[]; caption: string }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="border-b border-line text-left text-xs text-ink-3">
            {columns.map((c) => (
              <th key={c.header} scope="col" className={`px-2 py-2 font-medium ${c.numeric ? "text-right" : ""}`}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-line last:border-0">
              {columns.map((c) => (
                <td key={c.header} className={`px-2 py-2 text-ink ${c.numeric ? "tabular text-right" : ""}`}>
                  {c.cell(r)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Todo gráfico tem uma tabela equivalente: o valor nunca depende só do tooltip ou da cor. */
export function ChartOrTable({ chart, table }: { chart: ReactNode; table: ReactNode }) {
  const [asTable, setAsTable] = useState(false);
  return (
    <div>
      <div className="mb-2 flex justify-end">
        <button
          type="button"
          onClick={() => setAsTable((v) => !v)}
          className="rounded-md px-2.5 py-1 text-xs text-ink-2 shadow-[0_0_0_1px_var(--ring)] hover:bg-surface-2"
          aria-pressed={asTable}
        >
          {asTable ? "Ver gráfico" : "Ver tabela"}
        </button>
      </div>
      {asTable ? table : chart}
    </div>
  );
}

export function ChartTooltip({ title, rows }: { title: string; rows: { label: string; value: string; color?: string }[] }) {
  return (
    <div className="min-w-48 rounded-lg bg-surface px-3 py-2 text-xs shadow-lg shadow-black/10 ring-1 ring-[var(--ring)]">
      <div className="mb-1 font-medium text-ink-2">{title}</div>
      {rows.map((r) => (
        <div key={r.label} className="flex items-baseline justify-between gap-4 py-0.5">
          <span className="flex items-center gap-1.5 text-ink-3">
            {r.color ? <Swatch color={r.color} shape="line" /> : null}
            {r.label}
          </span>
          <span className="tabular font-semibold text-ink">{r.value}</span>
        </div>
      ))}
    </div>
  );
}
