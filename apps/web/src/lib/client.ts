"use client";

/** Chamadas feitas no navegador (administração, sorteador). Sempre via /api, na mesma origem. */
export class ClientError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ClientError";
    this.status = status;
  }
}

async function parse<T>(response: Response): Promise<T> {
  if (response.ok) {
    const type = response.headers.get("content-type") ?? "";
    return (type.includes("application/json") ? await response.json() : await response.text()) as T;
  }
  let detail = "Não foi possível concluir a operação.";
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") detail = body.detail;
    else if (Array.isArray(body.detail)) detail = "Confira os campos preenchidos.";
  } catch {
    /* sem corpo JSON */
  }
  throw new ClientError(response.status, detail);
}

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`/api${path}`, { credentials: "same-origin", cache: "no-store" });
  return parse<T>(response);
}

export async function sendJson<T>(
  method: "POST" | "PATCH" | "DELETE",
  path: string,
  body?: unknown,
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  return parse<T>(response);
}

export async function sendForm<T>(path: string, form: FormData): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: "POST",
    credentials: "same-origin",
    body: form,
  });
  return parse<T>(response);
}
