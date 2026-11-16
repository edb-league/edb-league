"use client";

import clsx from "clsx";
import { useCallback, useEffect, useState } from "react";
import { Feedback, useAction } from "@/components/admin/useAction";
import { SteamLogin } from "@/components/layout/UserMenu";
import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { getJson, sendJson } from "@/lib/client";
import type { LobbyMatchzy, LobbyView } from "@/lib/types";

const POLL_MS = 4000;
const FORMAT_LABEL = { md1: "MD1", md3: "MD3", md5: "MD5" } as const;

/** Lobby estilo XPlay: dois times de 5, o primeiro a entrar em cada um é o capitão. */
export function LobbyBoard({ avatars }: { avatars: Record<string, string> }) {
  const [view, setView] = useState<LobbyView | null>(null);
  const [failed, setFailed] = useState(false);
  const [match, setMatch] = useState<LobbyMatchzy | null>(null);
  const [copied, setCopied] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);
  const action = useAction();

  const refresh = useCallback(async () => {
    if (document.visibilityState === "hidden") return;
    try {
      setView(await getJson<LobbyView>("/lobby"));
      setFailed(false);
    } catch {
      setFailed(true);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(refresh, POLL_MS);
    document.addEventListener("visibilitychange", refresh);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", refresh);
    };
  }, [refresh]);

  async function change(run: () => Promise<LobbyView>) {
    const next = await action.run(run);
    if (next) {
      setView(next);
      setMatch(null);
    }
  }

  async function start() {
    const result = await action.run(() => getJson<LobbyMatchzy>("/lobby/matchzy"));
    if (result) setMatch(result);
  }

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* sem permissão: o texto continua selecionável */
    }
  }

  if (!view) {
    return <p className="text-muted" role="status">{failed ? "Sem conexão com a liga. Tentando de novo..." : "Carregando o lobby..."}</p>;
  }

  const { me } = view;
  function renderSlots(title: string, id: string, team: 0 | 1 | 2, players: LobbyView["spectators"]["players"], size: number) {
    return (
      <>
        <div className="flex items-center justify-between">
          <h2 id={id} className="text-2xl font-bold">{title}</h2>
          <span className="num text-lg text-muted">{players.length}/{size}</span>
        </div>
        <ul className="mt-3 flex flex-col gap-2">
          {Array.from({ length: size }, (_, slot) => {
            const player = players[slot];
            if (player) {
              const mine = player.id === me.player_id;
              return (
                <li key={slot} className={clsx("flex min-h-14 items-center gap-3 rounded-lg border px-3 py-1.5", mine ? "border-accent bg-surface-3" : "border-line-soft bg-surface-2")}>
                  <Avatar name={player.name} src={avatars[player.id]} size={40} level={player.level} decorative />
                  <span className="min-w-0 flex-1 text-lg font-bold break-words">{player.name}</span>
                  {team !== 0 && player.captain && (
                    <span className="inline-flex items-center gap-1 rounded-md bg-surface-3 px-2 py-0.5 text-sm font-bold text-gold">
                      <Icon name="star" /> Capitão
                    </span>
                  )}
                  {mine && (
                    <Button variant="ghost" disabled={action.busy} onClick={() => change(() => sendJson<LobbyView>("POST", "/lobby/leave"))}>
                      Sair
                    </Button>
                  )}
                  {me.is_admin && !mine && (
                    <Button variant="danger" disabled={action.busy} aria-label={`Remover ${player.name}`} onClick={() => change(() => sendJson<LobbyView>("DELETE", `/lobby/players/${player.id}`))}>
                      <Icon name="x" />
                    </Button>
                  )}
                </li>
              );
            }
            const canJoin = me.player_id !== null && me.team === null;
            return (
              <li key={slot} className="flex min-h-14 items-center justify-between gap-3 rounded-lg border border-dashed border-line px-3 py-1.5 text-muted">
                <span>{team === 0 ? "Vaga de espectador" : slot === 0 ? "Vaga de capitão" : "Vaga livre"}</span>
                {canJoin && (
                  <Button variant="secondary" disabled={action.busy} onClick={() => change(() => sendJson<LobbyView>("POST", "/lobby/join", { team }))}>
                    Entrar
                  </Button>
                )}
              </li>
            );
          })}
        </ul>
      </>
    );
  }
  const loggedIn = me.player_id !== null || me.is_admin;
  const mapName = view.maps.find((m) => m.id === view.map)?.name ?? view.map;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted" role="status">
          {failed ? "Sem conexão com a liga. Tentando de novo..." : "Atualiza sozinho a cada poucos segundos."}
        </p>
        {!loggedIn && <SteamLogin />}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {view.teams.map((team) => (
          <Card key={team.id} aria-labelledby={`time-${team.id}`} className={clsx("border-t-4", team.id === 1 ? "border-t-pt" : "border-t-pl")}>
            {renderSlots(`Time ${team.id}`, `time-${team.id}`, team.id, team.players, view.team_size)}
          </Card>
        ))}
      </div>

      <Card aria-labelledby="espectadores">
        {renderSlots("Espectadores", "espectadores", 0, view.spectators.players, view.spectators.slots)}
      </Card>

      <Card aria-labelledby="lobby-config" className="flex flex-col gap-4">
        <h2 id="lobby-config" className="text-2xl font-bold">Configurar lobby</h2>
        <p className="text-base text-muted">
          {me.can_configure ? "Você é capitão: escolha o mapa e o formato." : "Só os capitães (e o admin) escolhem o mapa e o formato."}
        </p>
        <div role="radiogroup" aria-label="Formato da partida" className="flex flex-wrap gap-2">
          {view.formats.map((f) => (
            <Button
              key={f.id}
              role="radio"
              aria-checked={view.format === f.id}
              variant={view.format === f.id ? "gold" : "secondary"}
              disabled={!me.can_configure || action.busy}
              onClick={() => change(() => sendJson<LobbyView>("PATCH", "/lobby", { format: f.id }))}
            >
              {FORMAT_LABEL[f.id]}
            </Button>
          ))}
        </div>
        <div role="radiogroup" aria-label={view.format === "md1" ? "Mapa" : "Mapa do jogo 1"} className="flex flex-wrap gap-2">
          {view.maps.map((m) => (
            <Button
              key={m.id}
              role="radio"
              aria-checked={view.map === m.id}
              variant={view.map === m.id ? "gold" : "secondary"}
              disabled={!me.can_configure || action.busy}
              onClick={() => change(() => sendJson<LobbyView>("PATCH", "/lobby", { map: m.id }))}
            >
              {m.name}
            </Button>
          ))}
        </div>
        {view.format !== "md1" && (
          <p className="text-sm text-muted">No {FORMAT_LABEL[view.format]}, {mapName} é o primeiro mapa e o restante sai do veto no servidor.</p>
        )}
      </Card>

      <Feedback error={action.error} ok={action.ok} />

      <Card aria-labelledby="lobby-start" className="flex flex-col gap-3">
        <h2 id="lobby-start" className="text-2xl font-bold">Iniciar partida</h2>
        <p className="num text-3xl">{view.count}/{view.team_size * 2} <span className="font-sans text-base font-medium text-muted">jogadores</span></p>
        <div className="flex flex-wrap gap-3">
          <Button variant="primary" disabled={!view.ready || !me.can_get_json || action.busy} onClick={start}>
            Iniciar partida
          </Button>
          {me.is_admin && (
            confirmReset ? (
              <Button variant="danger" disabled={action.busy} onClick={() => { setConfirmReset(false); void change(() => sendJson<LobbyView>("DELETE", "/lobby")); }}>
                Confirmar: esvaziar lobby
              </Button>
            ) : (
              <Button variant="ghost" onClick={() => setConfirmReset(true)}>Esvaziar lobby</Button>
            )
          )}
        </div>
        {!view.ready && <p className="text-base text-muted">A partida libera quando os dois times estiverem completos (5 contra 5).</p>}
        {view.ready && !me.can_get_json && <p className="text-base text-muted">Só quem está no lobby recebe o arquivo da partida.</p>}
        {match && (
          <div className="flex flex-col gap-3">
            <ol className="max-w-prose list-decimal space-y-1.5 pl-6 text-base text-muted">
              <li>Salve o texto abaixo como <code>edb.json</code> na pasta <code>cfg</code> do servidor.</li>
              <li>No console do servidor (ou como admin), digite <code>matchzy_loadmatch edb.json</code>.</li>
              <li>Todos entram no servidor: o MatchZy leva cada jogador direto para o seu time (espectadores vão para o espectador). Depois é só usar <code>.ready</code>.</li>
            </ol>
            <pre className="max-h-72 overflow-auto rounded-lg border border-line bg-surface p-3 text-sm">{match.json}</pre>
            <div><Button variant="secondary" onClick={() => copy(match.json)}>{copied ? "Copiado" : "Copiar JSON"}</Button></div>
          </div>
        )}
      </Card>
    </div>
  );
}
