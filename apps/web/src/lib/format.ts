import type { SeasonInfo } from "./types";

const formats = new Map<number, Intl.NumberFormat>();
function nf(decimals: number) {
  let f = formats.get(decimals);
  if (!f) {
    f = new Intl.NumberFormat("pt-BR", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
    formats.set(decimals, f);
  }
  return f;
}

/** Número em pt-BR; null, undefined e NaN viram "–". */
export function num(value: number | null | undefined, decimals = 0, suffix = ""): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "–";
  return nf(decimals).format(value) + suffix;
}

export function signed(value: number | null | undefined, decimals = 1, suffix = ""): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "–";
  const text = nf(decimals).format(Math.abs(value)) + suffix;
  if (value > 0) return `+${text}`;
  if (value < 0) return `-${text}`;
  return text;
}

/** "2026-10-19" -> "19/10/2026". */
export function dateBR(iso: string | null | undefined): string {
  if (!iso) return "Data não informada";
  const [y, m, d] = iso.slice(0, 10).split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

export function dayMonth(iso: string | null | undefined): string {
  if (!iso) return "";
  const [, m, d] = iso.slice(0, 10).split("-");
  return `${d}/${m}`;
}

/** Horas de CS, como no app atual (decimal abaixo de 10 h). */
export function hoursLabel(hours: number | null | undefined): string {
  if (hours === null || hours === undefined) return "–";
  if (hours === 0) return "0 h";
  if (hours < 10) return `${num(hours, 1)} h`;
  return `${new Intl.NumberFormat("pt-BR").format(Math.round(hours))} h`;
}

export function plural(n: number, one: string, many: string): string {
  return `${n} ${n === 1 ? one : many}`;
}

/** Texto de situação da temporada, equivalente ao da barra do Streamlit. */
export function seasonSummary(s: SeasonInfo): string {
  const done = plural(s.completed_series, "confronto concluído", "confrontos concluídos");
  switch (s.status) {
    case "active":
      return s.progress
        ? `Dia ${s.progress.day} de ${s.progress.total_days}, ${plural(s.progress.remaining, "dia restante", "dias restantes")}, ${done}`
        : done;
    case "upcoming":
      return `A iniciar: ${dayMonth(s.starts_on)} a ${dateBR(s.ends_on)}`;
    case "closed_pending":
      return `Encerrada, aguardando homologação, ${done}`;
    case "homologated":
      return `Homologada, ${done}`;
    default:
      return `${done}, calendário a confirmar`;
  }
}

export function seasonQuery(season: number | undefined, extra: Record<string, string | undefined> = {}): string {
  const params = new URLSearchParams();
  if (season !== undefined) params.set("temporada", String(season));
  for (const [k, v] of Object.entries(extra)) if (v) params.set(k, v);
  const text = params.toString();
  return text ? `?${text}` : "";
}

/** Lê ?temporada= de searchParams do Next. */
export function parseSeason(value: string | string[] | undefined): number | undefined {
  const raw = Array.isArray(value) ? value[0] : value;
  if (!raw) return undefined;
  const n = Number.parseInt(raw, 10);
  return Number.isInteger(n) && n >= 0 ? n : undefined;
}

export function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}
