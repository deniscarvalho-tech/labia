import type { Bundle } from "../lib/data";
import { byUnit, fmt } from "../lib/format";
import { Card, KindBadge } from "../components/ui";

export function Overview({ data }: { data: Bundle }) {
  const cards = data.summary.headline;
  const hero = cards[0];
  const rest = cards.slice(1);
  return (
    <div className="space-y-6">
      {hero ? (
        <section className="rounded-xl bg-surface p-6 shadow-[0_0_0_1px_var(--ring)]">
          <div className="flex flex-wrap items-center gap-2 text-sm text-ink-2">
            {hero.label} <KindBadge kind={hero.kind} />
          </div>
          <div className="mt-2 flex flex-wrap items-baseline gap-x-6 gap-y-2">
            <span className="text-6xl font-semibold tracking-tight text-ink">{byUnit(hero.unit, hero.value)}</span>
            {hero.comparison ? (
              <span className="text-lg text-ink-2">
                contra <strong className="font-semibold text-ink">{byUnit(hero.unit, hero.comparison.value)}</strong> do{" "}
                {hero.comparison.label}
              </span>
            ) : null}
          </div>
          <p className="mt-2 text-sm text-ink-3">
            {fmt.ci(hero.ci95)}
            {hero.note ? ` · ${hero.note}` : ""}
          </p>
        </section>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {rest.map((c) => (
          <article key={c.id} className="rounded-xl bg-surface p-5 shadow-[0_0_0_1px_var(--ring)]">
            <div className="flex items-center justify-between gap-2 text-sm text-ink-2">
              <span>{c.label}</span>
              <KindBadge kind={c.kind} />
            </div>
            <div className="mt-2 text-3xl font-semibold text-ink">{byUnit(c.unit, c.value)}</div>
            {c.comparison ? (
              <div className="mt-1 text-sm text-ink-2">
                {c.comparison.label}: <span className="font-medium text-ink">{byUnit(c.unit, c.comparison.value)}</span>
              </div>
            ) : null}
            <p className="mt-2 text-xs text-ink-3">{c.kind === "estimated" ? c.assumptions : fmt.ci(c.ci95)}</p>
          </article>
        ))}
      </div>

      <Card title="Como ler este painel">
        <ul className="grid gap-3 text-sm text-ink-2 md:grid-cols-3">
          <li>
            <strong className="text-ink">Fraude que passou:</strong> em quantas conversas de golpe o agente executou uma ação
            que a política proíbe. Quem decide é um verificador determinístico, que olha as ações, não o texto.
          </li>
          <li>
            <strong className="text-ink">Atrito:</strong> em quantas conversas com cliente honesto ele deixou de atender o que a
            pessoa tinha direito. Negar tudo zera a fraude e leva o atrito a 100%: as duas métricas andam juntas.
          </li>
          <li>
            <strong className="text-ink">Tática nunca vista:</strong> o pedido fatiado não aparece em nenhum exemplo de treino.
            É o teste de que o modelo aprendeu o princípio, e não decorou exemplos.
          </li>
        </ul>
      </Card>

      <Card title="Versões">
        <ol className="space-y-2 text-sm">
          {data.versions.versions.map((v) => (
            <li key={v.version} className="flex flex-wrap items-baseline gap-x-3">
              <span className="font-semibold text-ink">{v.version}</span>
              <span className="text-ink-2">{v.title}</span>
              <span className="text-xs text-ink-3">
                {v.status === "released" ? "publicada" : v.status === "in_progress" ? "em andamento" : "planejada"} ·{" "}
                {new Date(v.date + "T12:00:00").toLocaleDateString("pt-BR")}
              </span>
            </li>
          ))}
        </ol>
      </Card>
    </div>
  );
}
