"use client";

import { useEffect, useState } from "react";
import { Feedback, useAction } from "@/components/admin/useAction";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { getJson, sendJson } from "@/lib/client";
import type { DraftView, PlayerListItem } from "@/lib/types";
import { DraftBoard } from "./DraftBoard";
import { DraftSetup } from "./DraftSetup";

const POLL_MS = 5000;

/** Draft ao vivo para todos: atualiza sozinho a cada poucos segundos e qualquer visitante pode criar, escolher, desfazer e reiniciar. */
export function DraftLive({
  initial,
  avatars,
  players,
}: {
  initial: DraftView;
  avatars: Record<string, string>;
  players: PlayerListItem[];
}) {
  const [view, setView] = useState<DraftView>(initial);
  const [failed, setFailed] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);
  const action = useAction();

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

  async function change(run: () => Promise<DraftView>, success?: string) {
    const next = await action.run(run, success);
    if (next) setView(next);
  }

  if (!view.exists) return <DraftSetup players={players} onCreated={setView} />;

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted" role="status">
        {failed ? "Sem conexão com a liga. Tentando de novo..." : "Atualiza sozinho a cada poucos segundos."}
      </p>
      <Card aria-labelledby="draft-acoes" className="flex flex-col gap-3">
        <h2 id="draft-acoes" className="text-xl font-bold">Controle do draft</h2>
        <p className="text-base text-muted">
          Quando um capitão disser quem escolheu, toque em &quot;Escolher&quot; ao lado do jogador. Todos veem a mudança na hora.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="secondary"
            disabled={action.busy || view.picks_made === 0}
            onClick={() => change(() => sendJson<DraftView>("POST", "/draft/undo"), "Última escolha desfeita.")}
          >
            Desfazer última escolha
          </Button>
          {confirmReset ? (
            <>
              <Button
                variant="danger"
                disabled={action.busy}
                onClick={async () => {
                  setConfirmReset(false);
                  await change(() => sendJson<DraftView>("DELETE", "/draft"), "Draft reiniciado.");
                }}
              >
                Confirmar: apagar o draft
              </Button>
              <Button variant="ghost" onClick={() => setConfirmReset(false)}>Cancelar</Button>
            </>
          ) : (
            <Button variant="danger" disabled={action.busy} onClick={() => setConfirmReset(true)}>
              Reiniciar draft
            </Button>
          )}
        </div>
        <Feedback error={action.error} ok={action.ok} />
      </Card>
      <DraftBoard
        view={view}
        avatars={avatars}
        busy={action.busy}
        onPick={(playerId) => change(() => sendJson<DraftView>("POST", "/draft/pick", { player_id: playerId }))}
      />
    </div>
  );
}
