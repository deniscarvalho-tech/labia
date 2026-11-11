// Carrega os arquivos do contrato de dados. O painel não tem nenhum número próprio: tudo vem daqui.
import type { AuditFile } from "../contract/audit_findings";
import type { MetricRow, MetricsFile, MetricName, Sector, Split, Tactic } from "../contract/metrics";
import type { ReplayFile } from "../contract/replay";
import type { SummaryFile } from "../contract/summary";
import type { VersionsFile } from "../contract/versions";

export interface Bundle {
  summary: SummaryFile;
  metrics: MetricsFile;
  replay: ReplayFile;
  audit: AuditFile;
  versions: VersionsFile;
}

async function get<T>(name: string): Promise<T> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/${name}`);
  if (!response.ok) throw new Error(`não consegui ler ${name} (${response.status})`);
  return (await response.json()) as T;
}

export async function loadBundle(): Promise<Bundle> {
  const [summary, metrics, replay, audit, versions] = await Promise.all([
    get<SummaryFile>("summary.json"),
    get<MetricsFile>("metrics.json"),
    get<ReplayFile>("replay.json"),
    get<AuditFile>("audit_findings.json"),
    get<VersionsFile>("versions.json"),
  ]);
  return { summary, metrics, replay, audit, versions };
}

export function isSample(b: Bundle): boolean {
  return b.summary.is_sample || b.metrics.is_sample || b.replay.is_sample || b.audit.is_sample;
}

export interface Slice {
  sector: Sector;
  split: Split;
}

export function row(
  metrics: MetricsFile,
  model: string,
  metric: MetricName,
  slice: Slice,
  tactic: Tactic = "all",
): MetricRow | undefined {
  return metrics.rows.find(
    (r) =>
      r.model_id === model &&
      r.metric === metric &&
      r.sector === slice.sector &&
      r.split === slice.split &&
      r.tactic === tactic,
  );
}

/** A cor segue o modelo pela posição fixa dele na lista do contrato, nunca pela posição no ranking. */
export function modelColor(metrics: MetricsFile, model: string): string {
  const index = metrics.models.findIndex((m) => m.id === model);
  return `var(--series-${(index % 8) + 1})`;
}

export function modelLabel(metrics: MetricsFile, model: string): string {
  return metrics.models.find((m) => m.id === model)?.label ?? model;
}
