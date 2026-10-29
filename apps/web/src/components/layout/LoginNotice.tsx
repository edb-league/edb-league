"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";

const MESSAGES = {
  desconhecido: {
    tone: "warning",
    title: "Seu SteamID ainda não está cadastrado",
    text: "O login é só para jogadores da liga. Peça ao administrador para vincular o seu SteamID ao seu cadastro e tente de novo.",
  },
  erro: {
    tone: "error",
    title: "Não foi possível entrar com a Steam",
    text: "A Steam não confirmou o login. Tente de novo em alguns instantes.",
  },
} as const;

/** Aviso depois de uma tentativa de login que não deu certo (o motivo vem na URL: ?login=...). */
export function LoginNotice() {
  const reason = useSearchParams().get("login");
  const pathname = usePathname();
  const [dismissed, setDismissed] = useState<string | null>(null);
  const message = reason === "desconhecido" || reason === "erro" ? MESSAGES[reason] : null;
  if (!message || dismissed === reason) return null;

  function close() {
    setDismissed(reason);
    const url = new URL(window.location.href);
    url.searchParams.delete("login");
    window.history.replaceState(null, "", pathname + url.search);
  }

  return (
    <div className="reveal mx-auto w-full max-w-7xl px-4 pt-4 md:px-8">
      <Notice tone={message.tone} title={message.title}>
        <p>{message.text}</p>
        <Button variant="secondary" className="mt-3" onClick={close}>
          Entendi
        </Button>
      </Notice>
    </div>
  );
}
