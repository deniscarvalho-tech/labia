import type { Bundle } from "../lib/data";
import { modelLabel } from "../lib/data";
import { fmt } from "../lib/format";
import { SECTOR, TACTIC, TRUST_LINK } from "../lib/labels";
import { Card, SeverityPill } from "../components/ui";

export function Audit({ data, onEvidence }: { data: Bundle; onEvidence: (conversationId: string) => void }) {
  const a = data.audit;
  const inReplay = new Set(data.replay.conversations.map((c) => c.id));
  return (
    <div className="space-y-4">
      <Card
        title="Relatório de auditoria"
        subtitle="O mesmo formato de um relatório de auditoria interna: escopo, achados com severidade, evidência, causa raiz, recomendação e reteste. A severidade sai de uma matriz fixa de frequência × valor em risco, definida antes dos resultados."
      >
        <dl className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <dt className="text-xs text-ink-3">Agentes</dt>
            <dd className="text-ink">{a.scope.agents.map((id) => modelLabel(data.metrics, id).replace(/^Exemplo: /, "")).join(", ")}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-3">Setores</dt>
            <dd className="text-ink">{a.scope.sectors.map((s) => SECTOR[s]).join(", ")}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-3">Táticas</dt>
            <dd className="text-ink">{a.scope.tactics.map((t) => TACTIC[t]).join(", ")}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-3">Conversas analisadas</dt>
            <dd className="tabular text-ink">{fmt.num(a.scope.n_conversations)}</dd>
          </div>
        </dl>
      </Card>
      {a.findings.map((f) => (
        <article key={f.id} className="rounded-xl bg-surface p-5 shadow-[0_0_0_1px_var(--ring)]">
          <header className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs text-ink-3">{f.id}</span>
            <SeverityPill severity={f.severity} />
            <span className="text-xs text-ink-3">
              Regra {f.rule_ids.join(", ")} · {TRUST_LINK[f.trust_link]}
            </span>
          </header>
          <h3 className="mt-2 text-base font-semibold text-ink">{f.title}</h3>
          <dl className="mt-3 grid gap-4 text-sm md:grid-cols-3">
            <div>
              <dt className="text-xs text-ink-3">Frequência nos golpes desta regra</dt>
              <dd className="text-ink">
                <span className="text-xl font-semibold">{fmt.pct(f.frequency.value)}</span>{" "}
                <span className="text-xs text-ink-3">{fmt.ci(f.frequency.ci95)}</span>
              </dd>
            </div>
            <div>
              <dt className="text-xs text-ink-3">Valor em risco por mil conversas</dt>
              <dd className="text-xl font-semibold text-ink">{fmt.brl(f.value_at_risk_brl_per_1k)}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-3">Reteste</dt>
              <dd className="text-ink">{f.retest.status === "not_retested" ? "ainda não retestado" : f.retest.status === "fixed" ? `corrigido na ${f.retest.version}` : "continua falhando"}</dd>
            </div>
          </dl>
          <div className="mt-4 grid gap-4 text-sm md:grid-cols-2">
            <div>
              <h4 className="text-xs font-medium text-ink-3">Causa raiz</h4>
              <p className="mt-1 text-ink">{f.root_cause}</p>
            </div>
            <div>
              <h4 className="text-xs font-medium text-ink-3">Recomendação</h4>
              <p className="mt-1 text-ink">{f.recommendation}</p>
            </div>
          </div>
          <div className="mt-4 text-sm">
            <h4 className="text-xs font-medium text-ink-3">Evidências</h4>
            <ul className="mt-1 flex flex-wrap gap-2">
              {f.evidence.map((id) => (
                <li key={id}>
                  {inReplay.has(id) ? (
                    <button type="button" onClick={() => onEvidence(id)}
                      className="rounded-md px-2 py-1 font-mono text-xs text-accent shadow-[0_0_0_1px_var(--ring)] hover:bg-surface-2">
                      {id} → replay
                    </button>
                  ) : (
                    <span className="rounded-md px-2 py-1 font-mono text-xs text-ink-3 shadow-[0_0_0_1px_var(--ring)]">{id}</span>
                  )}
                </li>
              ))}
            </ul>
            <p className="mt-1 text-xs text-ink-3">Afeta: {f.models_affected.map((id) => modelLabel(data.metrics, id).replace(/^Exemplo: /, "")).join(", ")}</p>
          </div>
        </article>
      ))}
    </div>
  );
}
