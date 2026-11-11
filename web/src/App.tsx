import { useEffect, useState } from "react";
import type { Sector, Split } from "./contract/metrics";
import { isSample, loadBundle, type Bundle, type Slice } from "./lib/data";
import { fmt } from "./lib/format";
import { SECTOR, SPLIT } from "./lib/labels";
import { SampleBanner } from "./components/ui";
import { Audit } from "./views/Audit";
import { FraudFriction } from "./views/FraudFriction";
import { Overview } from "./views/Overview";
import { Ranking } from "./views/Ranking";
import { Replay } from "./views/Replay";
import { Resistance } from "./views/Resistance";
import { TacticMap } from "./views/TacticMap";

const VIEWS = [
  { id: "visao-geral", label: "Visão geral" },
  { id: "fraude-atrito", label: "Fraude × atrito" },
  { id: "ranking", label: "Ranking" },
  { id: "taticas", label: "Mapa de táticas" },
  { id: "resistencia", label: "Resistência por turno" },
  { id: "replay", label: "Replay" },
  { id: "auditoria", label: "Auditoria" },
] as const;
type ViewId = (typeof VIEWS)[number]["id"];
const SLICED: ViewId[] = ["fraude-atrito", "ranking", "taticas", "resistencia"];

function readHash(): { view: ViewId; conversation: string | null } {
  const [view, conversation] = window.location.hash.replace(/^#\/?/, "").split("/");
  const known = VIEWS.some((v) => v.id === view);
  return { view: known ? (view as ViewId) : "visao-geral", conversation: conversation ? decodeURIComponent(conversation) : null };
}

function storedTheme(): "light" | "dark" | null {
  try {
    const t = localStorage.getItem("labia-tema");
    return t === "light" || t === "dark" ? t : null;
  } catch {
    return null;
  }
}

export function App() {
  const [data, setData] = useState<Bundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [route, setRoute] = useState(readHash);
  const [slice, setSlice] = useState<Slice>({ sector: "all", split: "seen_tactics" });
  const [theme, setTheme] = useState<"light" | "dark" | null>(storedTheme);

  useEffect(() => {
    loadBundle().then(setData).catch((e: Error) => setError(e.message));
    const onHash = () => setRoute(readHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    if (theme) document.documentElement.dataset.theme = theme;
    else delete document.documentElement.dataset.theme;
    try {
      if (theme) localStorage.setItem("labia-tema", theme);
    } catch {
      /* armazenamento indisponível: o tema só não fica lembrado */
    }
  }, [theme]);

  const go = (view: ViewId, conversation?: string) => {
    window.location.hash = conversation ? `/${view}/${encodeURIComponent(conversation)}` : `/${view}`;
  };
  const dark = theme === "dark" || (theme === null && window.matchMedia("(prefers-color-scheme: dark)").matches);

  if (error) {
    return <p className="p-8 text-critical">Erro ao carregar os dados: {error}</p>;
  }
  if (!data) {
    return <p className="p-8 text-ink-2">Carregando os resultados…</p>;
  }
  const sectors = [...new Set(data.metrics.rows.map((r) => r.sector))] as Sector[];
  const splits: Split[] = ["seen_tactics", "heldout_tactic", "all_test"];

  return (
    <div className="min-h-screen">
      {isSample(data) ? <SampleBanner /> : null}
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div>
            <h1 className="text-xl font-semibold text-ink">Lábia</h1>
            <p className="text-sm text-ink-2">Um LLM pequeno e aberto treinado para não cair em engenharia social em português.</p>
          </div>
          <div className="flex items-center gap-3 text-xs text-ink-3">
            <span>
              {data.metrics.release} · commit <span className="font-mono">{data.metrics.git_sha}</span> · gerado em{" "}
              {fmt.date(data.metrics.generated_at)}
            </span>
            <button
              type="button"
              onClick={() => setTheme(dark ? "light" : "dark")}
              className="rounded-md px-2.5 py-1 text-ink-2 shadow-[0_0_0_1px_var(--ring)] hover:bg-surface-2"
            >
              {dark ? "Tema claro" : "Tema escuro"}
            </button>
          </div>
        </div>
        <nav className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4" aria-label="Seções do painel">
          {VIEWS.map((v) => (
            <a
              key={v.id}
              href={`#/${v.id}`}
              aria-current={route.view === v.id ? "page" : undefined}
              className={`whitespace-nowrap border-b-2 px-3 py-2 text-sm ${
                route.view === v.id ? "border-accent font-medium text-ink" : "border-transparent text-ink-2 hover:text-ink"
              }`}
            >
              {v.label}
            </a>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
        {SLICED.includes(route.view) ? (
          <div className="flex flex-wrap items-end gap-3" role="group" aria-label="Filtros">
            <label className="flex flex-col gap-1 text-xs text-ink-3">
              Setor
              <select
                value={slice.sector}
                onChange={(e) => setSlice((s) => ({ ...s, sector: e.target.value as Sector }))}
                className="rounded-md bg-surface px-2 py-1.5 text-sm text-ink shadow-[0_0_0_1px_var(--ring)]"
              >
                {sectors.map((s) => (
                  <option key={s} value={s}>
                    {SECTOR[s]}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-xs text-ink-3">
              Divisão do teste
              <select
                value={slice.split}
                onChange={(e) => setSlice((s) => ({ ...s, split: e.target.value as Split }))}
                className="rounded-md bg-surface px-2 py-1.5 text-sm text-ink shadow-[0_0_0_1px_var(--ring)]"
              >
                {splits.map((s) => (
                  <option key={s} value={s}>
                    {SPLIT[s]}
                  </option>
                ))}
              </select>
            </label>
          </div>
        ) : null}

        {route.view === "visao-geral" && <Overview data={data} />}
        {route.view === "fraude-atrito" && <FraudFriction data={data} slice={slice} />}
        {route.view === "ranking" && <Ranking data={data} slice={slice} />}
        {route.view === "taticas" && <TacticMap data={data} slice={slice} />}
        {route.view === "resistencia" && <Resistance data={data} slice={slice} />}
        {route.view === "replay" && <Replay data={data} selected={route.conversation} onSelect={(id) => go("replay", id)} />}
        {route.view === "auditoria" && <Audit data={data} onEvidence={(id) => go("replay", id)} />}
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-10 text-xs text-ink-3">
        Todos os números saem de <span className="font-mono">results/*.json</span>, gerados por script a partir das conversas
        julgadas pelo verificador. Código, plano pré-registrado e dados em{" "}
        <a className="text-accent underline" href="https://github.com/deniscarvalho-tech/labia">
          github.com/deniscarvalho-tech/labia
        </a>
        .
      </footer>
    </div>
  );
}
