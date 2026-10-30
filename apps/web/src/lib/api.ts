import { notFound } from "next/navigation";

/** URL interna da API; só o servidor Next.js a usa. O navegador fala com /api (proxy). */
export const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function qs(params: Record<string, string | number | boolean | undefined>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") sp.set(k, String(v));
  }
  const text = sp.toString();
  return text ? `?${text}` : "";
}

/** Respostas de "API ainda acordando" (Render gratuito) e de gateway: vale tentar de novo. */
const WAKING = new Set([502, 503, 504]);
const RETRIES = 2;
const RETRY_DELAY_MS = 2500;

/** GET com poucas novas tentativas quando a API está subindo; falha de rede também conta. */
async function fetchWithRetry(url: string, revalidate: number): Promise<Response> {
  for (let attempt = 0; ; attempt++) {
    try {
      const response = await fetch(url, { next: { revalidate } });
      if (!WAKING.has(response.status) || attempt >= RETRIES) return response;
    } catch (error) {
      if (attempt >= RETRIES) throw error;
    }
    await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
  }
}

/** Consulta a API no servidor, com cache curto (os dados da liga mudam poucas vezes por dia). */
export async function api<T>(path: string, options: { revalidate?: number } = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetchWithRetry(`${API_URL}/api${path}`, options.revalidate ?? 30);
  } catch {
    throw new ApiError(503, "Não foi possível conectar à API da liga. Tente novamente em instantes.");
  }
  if (!response.ok) {
    let detail = "A API da liga respondeu com erro.";
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* corpo não era JSON */
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

/** Igual a api(), mas converte 404/400 em página 404. */
export async function apiOrNotFound<T>(path: string, options: { revalidate?: number } = {}): Promise<T> {
  try {
    return await api<T>(path, options);
  } catch (error) {
    if (error instanceof ApiError && (error.status === 404 || error.status === 400)) notFound();
    throw error;
  }
}

/** Fotos da Steam por jogador. Nunca falha: sem chave, sem SteamID ou com a Steam fora do ar volta vazio. */
export async function steamAvatars(): Promise<Record<string, string>> {
  try {
    return await api<Record<string, string>>("/steam/avatars", { revalidate: 600 });
  } catch {
    return {};
  }
}
