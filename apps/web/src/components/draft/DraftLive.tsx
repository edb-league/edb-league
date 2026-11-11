"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { getJson } from "@/lib/client";
import type { DraftView } from "@/lib/types";
import { DraftBoard } from "./DraftBoard";

const POLL_MS = 5000;

/** Mostra o draft e o atualiza sozinho a cada poucos segundos (só com a aba visível). */
export function DraftLive({ initial, avatars }: { initial: DraftView; avatars: Record<string, string> }) {
  const [view, setView] = useState<DraftView>(initial);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function refresh() {
      if (document.visibilityState === "hidden") return;
      try {
        const next = await getJson<DraftView>("/draft");
        if (!cancelled) {
          setView(next);
          setFailed(false);
        }
      } catch {
        if (!cancelled) setFailed(true);
      }
    }
    const timer = window.setInterval(refresh, POLL_MS);
    document.addEventListener("visibilitychange", refresh);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", refresh);
    };
  }, []);

  if (!view.exists) {
    return (
      <Card>
        <p className="text-lg">Nenhum draft em andamento. Quando o administrador criar um, ele aparece aqui ao vivo.</p>
      </Card>
    );
  }
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-muted" role="status">
        {failed ? "Sem conexão com a liga. Tentando de novo..." : "Atualiza sozinho a cada poucos segundos."}
      </p>
      <DraftBoard view={view} avatars={avatars} />
    </div>
  );
}
