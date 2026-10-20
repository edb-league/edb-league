import { api } from "./api";
import { parseSeason } from "./format";
import type { Meta } from "./types";

/** Lê a temporada pedida em ?temporada= e cai na vigente se não existir. */
export async function seasonContext(raw: string | string[] | undefined): Promise<{ meta: Meta; season: number }> {
  const meta = await api<Meta>("/meta");
  const requested = parseSeason(raw);
  const exists = requested !== undefined && requested >= 1 && meta.seasons.some((s) => s.number === requested);
  return { meta, season: exists ? requested : meta.current_season };
}
