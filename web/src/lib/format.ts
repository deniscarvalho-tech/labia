const pct0 = new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 0 });
const pct1 = new Intl.NumberFormat("pt-BR", { style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 1 });
const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const brl2 = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const usd = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "USD", maximumFractionDigits: 2 });
const num = new Intl.NumberFormat("pt-BR");
const compact = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });

const pct = (v: number): string => (v < 0.1 && v > 0 ? pct1.format(v) : pct0.format(v));

export const fmt = {
  pct,
  pct1: (v: number) => pct1.format(v),
  brl: (v: number) => brl.format(v),
  brl2: (v: number) => brl2.format(v),
  brlCompact: (v: number) => `R$ ${compact.format(v)}`,
  usd: (v: number) => usd.format(v),
  num: (v: number) => num.format(v),
  ci: (ci: [number, number] | null | undefined, f: (v: number) => string = pct): string =>
    ci ? `IC 95%: ${f(ci[0])} a ${f(ci[1])}` : "sem IC",
  date: (iso: string) =>
    new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short", timeZone: "America/Sao_Paulo" }),
};

export function byUnit(unit: string, value: number): string {
  if (unit === "ratio") return fmt.pct(value);
  if (unit === "usd") return fmt.usd(value);
  if (unit === "brl") return fmt.brl(value);
  if (unit === "seconds") return `${value.toFixed(2)} s`;
  return fmt.num(value);
}
