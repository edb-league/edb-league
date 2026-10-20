import { notFound } from "next/navigation";

/** URL interna da API; só o servidor Next.js a usa. O navegador fala com /api (proxy). */
const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

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

/** Consulta a API no servidor, com cache curto (os dados da liga mudam poucas vezes por dia). */
export async function api<T>(path: string, options: { revalidate?: number } = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api${path}`, {
      next: { revalidate: options.revalidate ?? 30 },
    });
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
