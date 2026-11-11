import { useMemo, useState } from "react";
import type { AgentMessage, ReplayConversation, Verdict } from "../contract/replay";
import type { Bundle } from "../lib/data";
import { modelColor, modelLabel } from "../lib/data";
import { fmt } from "../lib/format";
import { SECTOR, TACTIC, TOOL, TRUST_LINK, VERDICT } from "../lib/labels";
import { Card, Swatch, VerdictPill } from "../components/ui";

function Select<T extends string>({ label, value, options, onChange }: {
  label: string;
  value: T | "";
  options: { value: T; label: string }[];
  onChange: (v: T | "") => void;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs text-ink-3">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as T | "")}
        className="rounded-md bg-surface px-2 py-1.5 text-sm text-ink shadow-[0_0_0_1px_var(--ring)]"
      >
        <option value="">Todos</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function ToolChip({ name, args, valid }: { name: string; args: Record<string, unknown>; valid: boolean }) {
  const shown = Object.entries(args)
    .filter(([k]) => k !== "relato")
    .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : String(v)}`)
    .join(" · ");
  return (
    <div className="rounded-md bg-surface-2 px-2.5 py-1.5 text-xs">
      <span className="font-mono font-medium text-ink">{name}</span>
      {!valid ? <span className="ml-2 font-medium text-critical">chamada inválida</span> : null}
      <span className="ml-1 text-ink-3">({TOOL[name] ?? "ferramenta"})</span>
      {shown ? <div className="mt-0.5 break-words font-mono text-ink-2">{shown}</div> : null}
    </div>
  );
}

function Conversation({ conv, data }: { conv: ReplayConversation; data: Bundle }) {
  const toolResults = conv.messages.filter((m) => m.role === "tool");
  let toolIndex = 0;
  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <VerdictPill verdict={conv.verdict as Verdict} />
        <span className="flex items-center gap-1.5 text-sm text-ink-2">
          <Swatch color={modelColor(data.metrics, conv.model_id)} />
          {modelLabel(data.metrics, conv.model_id).replace(/^Exemplo: /, "")}
        </span>
        <span className="text-sm text-ink-3">
          {SECTOR[conv.sector]} · {TACTIC[conv.tactic]} · {conv.legit ? "cliente honesto" : "golpe"} · rodada {conv.run}
        </span>
      </div>
      {conv.violated_rules.length ? (
        <p className="mt-2 text-sm text-ink-2">
          Regra violada: <strong className="text-ink">{conv.violated_rules.join(", ")}</strong>
          {conv.trust_link ? ` · elo de confiança: ${TRUST_LINK[conv.trust_link]}` : ""} · valor em risco:{" "}
          <strong className="text-ink">{fmt.brl2(conv.value_at_risk_brl)}</strong>
        </p>
      ) : null}
      <ol className="mt-4 space-y-3">
        {conv.messages.map((msg, i) => {
          if (msg.role === "tool") return null;
          const isAgent = msg.role === "agent";
          const conceded = isAgent && conv.concession_turn === msg.turn && (msg as AgentMessage).tool_calls?.length;
          const calls = isAgent ? (msg as AgentMessage).tool_calls ?? [] : [];
          const results = calls.map(() => toolResults[toolIndex++]);
          return (
            <li key={i} className={`flex ${isAgent ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
                  isAgent ? "bg-surface-2" : "bg-surface shadow-[0_0_0_1px_var(--ring)]"
                } ${conceded ? "ring-2 ring-[var(--status-critical)]" : ""}`}
              >
                <div className="mb-1 text-xs text-ink-3">
                  {isAgent ? "Agente" : "Cliente"} · turno {msg.turn}
                </div>
                {conceded && conv.highlight ? (
                  <div className="mb-2 flex items-start gap-1.5 rounded-md bg-highlight px-2 py-1.5 text-xs font-medium text-critical">
                    <span aria-hidden>●</span>
                    {conv.highlight.text}
                  </div>
                ) : null}
                {calls.length ? (
                  <div className="mb-2 space-y-1.5">
                    {calls.map((c, j) => (
                      <div key={j}>
                        <ToolChip name={c.name} args={c.arguments} valid={c.valid} />
                        {results[j] ? (
                          <details className="ml-2 mt-1 text-xs text-ink-3">
                            <summary className="cursor-pointer">resposta do sistema</summary>
                            <pre className="mt-1 max-h-48 overflow-auto rounded bg-surface p-2 text-[11px] text-ink-2">
                              {JSON.stringify(results[j]?.content, null, 2)}
                            </pre>
                          </details>
                        ) : null}
                      </div>
                    ))}
                  </div>
                ) : null}
                {msg.content ? <p className="whitespace-pre-wrap text-ink">{String(msg.content)}</p> : null}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export function Replay({ data, selected, onSelect }: { data: Bundle; selected: string | null; onSelect: (id: string) => void }) {
  const convs = data.replay.conversations;
  const [model, setModel] = useState("");
  const [tactic, setTactic] = useState("");
  const [verdict, setVerdict] = useState("");
  const filtered = useMemo(
    () =>
      convs.filter(
        (c) => (!model || c.model_id === model) && (!tactic || c.tactic === tactic) && (!verdict || c.verdict === verdict),
      ),
    [convs, model, tactic, verdict],
  );
  const current = convs.find((c) => c.id === selected) ?? filtered[0];
  const tactics = [...new Set(convs.map((c) => c.tactic))];
  const verdicts = [...new Set(convs.map((c) => c.verdict))] as Verdict[];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <Select label="Modelo" value={model} onChange={setModel}
          options={data.metrics.models.map((m) => ({ value: m.id, label: m.label.replace(/^Exemplo: /, "") }))} />
        <Select label="Tática" value={tactic} onChange={setTactic} options={tactics.map((t) => ({ value: t, label: TACTIC[t] }))} />
        <Select label="Veredito" value={verdict} onChange={setVerdict} options={verdicts.map((v) => ({ value: v, label: VERDICT[v] }))} />
      </div>
      <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
        <Card title={`${filtered.length} conversas`}>
          <ul className="max-h-[640px] space-y-1 overflow-y-auto pr-1">
            {filtered.map((c) => (
              <li key={c.id}>
                <button
                  type="button"
                  onClick={() => onSelect(c.id)}
                  className={`w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-surface-2 ${
                    current?.id === c.id ? "bg-surface-2 shadow-[0_0_0_1px_var(--ring)]" : ""
                  }`}
                >
                  <div className="flex items-center gap-1.5 text-ink">
                    <Swatch color={modelColor(data.metrics, c.model_id)} />
                    {VERDICT[c.verdict as Verdict]}
                  </div>
                  <div className="mt-0.5 text-xs text-ink-3">
                    {TACTIC[c.tactic]} · {c.legit ? "honesto" : "golpe"} · {c.scenario_id.split("-").slice(1, 3).join("-")}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </Card>
        <Card title="Conversa" subtitle={current ? <span className="font-mono text-xs">{current.id}</span> : undefined}>
          {current ? <Conversation conv={current} data={data} /> : <p className="text-sm text-ink-2">Nenhuma conversa com esses filtros.</p>}
        </Card>
      </div>
    </div>
  );
}
