import { cookies } from "next/headers";
import { cache } from "react";
import { API_URL } from "@/lib/api";
import type { Me } from "@/lib/types";

const ANONYMOUS: Me = { login_enabled: false, authenticated: false, is_admin: false, player: null, avatar: null };

/**
 * Quem está vendo a página. Só o cookie da sessão é repassado à API (nenhum outro). Sem cookie, a resposta
 * é a mesma para todos e pode ficar em cache; com cookie, nunca. Se a API falhar, o site segue como visitante.
 */
export const getMe = cache(async (): Promise<Me> => {
  try {
    const session = (await cookies()).get("edb_session")?.value;
    const response = await fetch(
      `${API_URL}/api/me`,
      session
        ? { headers: { cookie: `edb_session=${session}` }, cache: "no-store" }
        : { next: { revalidate: 300 } },
    );
    if (!response.ok) return ANONYMOUS;
    return (await response.json()) as Me;
  } catch {
    return ANONYMOUS;
  }
});
