"use client";

import { useEffect, useMemo, useState } from "react";
import { DraftBoard } from "@/components/draft/DraftBoard";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { CheckboxField, SelectField, TextField } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { getJson, sendJson } from "@/lib/client";
import type { AdminPlayer, DraftView } from "@/lib/types";
import { Feedback, useAction } from "./useAction";

const DEFAULT_NAMES = ["Time 1", "Time 2", "Time 3", "Time 4", "Time 5", "Time 6", "Time 7", "Time 8"];

function SetupForm({ players, onCreated }: { players: AdminPlayer[]; onCreated: (view: DraftView) => void }) {
  const active = useMemo(() => players.filter((p) => p.is_active), [players]);
  const [name, setName] = useState("");
  const [teamCount, setTeamCount] = useState(4);
  const [teamSize, setTeamSize] = useState(5);
  const [teamNames, setTeamNames] = useState<string[]>(DEFAULT_NAMES);
  const [captains, setCaptains] = useState<string[]>(Array(8).fill(""));
  const [pool, setPool] = useState<string[]>([]);
  const action = useAction();

  const chosenCaptains = captains.slice(0, teamCount).filter(Boolean);
  const needed = teamCount * (teamSize - 1);
  const poolIds = pool.filter((id) => !chosenCaptains.includes(id));
  const ready = name.trim() !== "" && chosenCaptains.length === teamCount && new Set(chosenCaptains).size === teamCount && poolIds.length === needed;

  function shuffleOrder() {
    const order = captains.slice(0, teamCount).map((captain, i) => ({ captain, team: teamNames[i] ?? "" }));
    for (let i = order.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [order[i], order[j]] = [order[j]!, order[i]!];
    }
    setCaptains([...order.map((o) => o.captain), ...captains.slice(teamCount)]);
    setTeamNames([...order.map((o) => o.team), ...teamNames.slice(teamCount)]);
  }

  return (
    <Card aria-labelledby="draft-novo">
      <h3 id="draft-novo" className="text-xl font-bold">Criar draft</h3>
      <p className="mb-4 text-base text-muted">
        Defina os times e capitães e marque todos os jogadores que serão escolhidos. A ordem dos times abaixo é a ordem da 1ª rodada; nas
        rodadas seguintes ela se inverte (cobra).
      </p>
      <form
        className="flex flex-col gap-5"
        onSubmit={async (event) => {
          event.preventDefault();
          const view = await action.run(
            () =>
              sendJson<DraftView>("POST", "/admin/draft", {
                name: name.trim(),
                team_size: teamSize,
                teams: Array.from({ length: teamCount }, (_, i) => ({ name: (teamNames[i] ?? "").trim(), captain_id: captains[i] ?? "" })),
                pool_ids: poolIds,
              }),
            "Draft criado.",
          );
          if (view) onCreated(view);
        }}
      >
        <div className="grid gap-4 md:grid-cols-3">
          <TextField id="draft-nome" label="Nome do campeonato" value={name} onChange={(e) => setName(e.target.value)} maxLength={60} placeholder="Ex.: Copa EDB" />
          <SelectField id="draft-times" label="Quantidade de times" value={teamCount} onChange={(e) => setTeamCount(Number(e.target.value))}>
            {[2, 3, 4, 5, 6, 7, 8].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </SelectField>
          <SelectField id="draft-tamanho" label="Jogadores por time (com o capitão)" value={teamSize} onChange={(e) => setTeamSize(Number(e.target.value))}>
            {[2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </SelectField>
        </div>

        <fieldset className="flex flex-col gap-3">
          <legend className="text-base font-bold">Times e capitães, na ordem da 1ª rodada</legend>
          {Array.from({ length: teamCount }, (_, i) => (
            <div key={i} className="grid gap-3 sm:grid-cols-2">
              <TextField
                id={`draft-time-${i}`}
                label={`Nome do time ${i + 1}`}
                value={teamNames[i] ?? ""}
                maxLength={30}
                onChange={(e) => setTeamNames((cur) => cur.map((n, j) => (j === i ? e.target.value : n)))}
              />
              <SelectField
                id={`draft-cap-${i}`}
                label={`Capitão do time ${i + 1}`}
                value={captains[i] ?? ""}
                onChange={(e) => setCaptains((cur) => cur.map((c, j) => (j === i ? e.target.value : c)))}
              >
                <option value="">Escolha o capitão</option>
                {active.map((p) => (
                  <option key={p.id} value={p.id} disabled={captains.some((c, j) => c === p.id && j !== i && j < teamCount)}>
                    {p.name} (nível {p.level})
                  </option>
                ))}
              </SelectField>
            </div>
          ))}
          <div>
            <Button variant="secondary" onClick={shuffleOrder}>Sortear a ordem dos times</Button>
          </div>
        </fieldset>

        <fieldset className="flex flex-col gap-2">
          <legend className="text-base font-bold">Jogadores a escolher</legend>
          <p className={poolIds.length === needed ? "text-base text-win" : "text-base text-muted"} role="status">
            {poolIds.length} de {needed} selecionados (sem contar os capitães).
          </p>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {active
              .filter((p) => !chosenCaptains.includes(p.id))
              .map((p) => (
                <CheckboxField
                  key={p.id}
                  id={`draft-pool-${p.id}`}
                  label={`${p.name} (nível ${p.level})`}
                  checked={pool.includes(p.id)}
                  onChange={(e) => setPool((cur) => (e.target.checked ? [...cur, p.id] : cur.filter((x) => x !== p.id)))}
                />
              ))}
          </div>
        </fieldset>

        <div>
          <Button variant="gold" type="submit" disabled={!ready || action.busy}>
            {action.busy ? "Criando..." : "Criar draft"}
          </Button>
        </div>
        <Feedback error={action.error} ok={action.ok} />
      </form>
    </Card>
  );
}

/** Administração do draft: cria, registra cada escolha na vez do capitão, desfaz e reinicia. */
export function DraftTab({ players }: { players: AdminPlayer[] }) {
  const [view, setView] = useState<DraftView | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);
  const action = useAction();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const current = await getJson<DraftView>("/draft");
        if (!cancelled) setView(current);
      } catch (e) {
        if (!cancelled) setLoadError(e instanceof Error ? e.message : "Não foi possível carregar o draft.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loadError) return <Notice tone="error">{loadError}</Notice>;
  if (!view) return <p role="status" className="text-base text-muted">Carregando draft...</p>;
  if (!view.exists) return <SetupForm players={players} onCreated={setView} />;

  async function change(run: () => Promise<DraftView>, success?: string) {
    const next = await action.run(run, success);
    if (next) setView(next);
  }

  return (
    <div className="flex flex-col gap-4">
      <Card aria-labelledby="draft-acoes" className="flex flex-col gap-3">
        <h3 id="draft-acoes" className="text-xl font-bold">Controle do draft</h3>
        <p className="text-base text-muted">
          Quando um capitão disser quem escolheu, toque em &quot;Escolher&quot; ao lado do jogador. A página pública atualiza sozinha.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="secondary" disabled={action.busy || view.picks_made === 0} onClick={() => change(() => sendJson<DraftView>("POST", "/admin/draft/undo"), "Última escolha desfeita.")}>
            Desfazer última escolha
          </Button>
          {confirmReset ? (
            <>
              <Button
                variant="danger"
                disabled={action.busy}
                onClick={async () => {
                  setConfirmReset(false);
                  await change(() => sendJson<DraftView>("DELETE", "/admin/draft"), "Draft reiniciado.");
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
        busy={action.busy}
        onPick={(playerId) => change(() => sendJson<DraftView>("POST", "/admin/draft/pick", { player_id: playerId }))}
      />
    </div>
  );
}
