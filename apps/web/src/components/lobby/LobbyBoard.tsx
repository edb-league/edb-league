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
  const [showMaps, setShowMaps] = useState(false);
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
    const first = window.setTimeout(refresh, 0);
    const timer = window.setInterval(refresh, POLL_MS);
    document.addEventListener("visibilitychange", refresh);
    return () => {
      window.clearTimeout(first);
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

  const v: LobbyView = view;
  const { me } = v;
  const loggedIn = me.player_id !== null || me.is_admin;
  const mapName = view.maps.find((m) => m.id === view.map)?.name ?? view.map;
  const canJoin = me.player_id !== null && me.team === null;

  function row(player: LobbyView["spectators"]["players"][number] | undefined, team: 0 | 1 | 2, slot: number, compact = false) {
    if (player) {
      const mine = player.id === me.player_id;
      return (
        <li key={slot} className={clsx("flex items-center gap-3 rounded-xl border px-3", compact ? "min-h-14" : "min-h-16", mine ? "border-accent bg-surface-3" : "border-line-soft bg-surface-2")}>
          <Avatar name={player.name} src={avatars[player.id]} size={40} level={player.level} decorative />
          <span className="min-w-0 flex-1">
            <span className="block text-lg font-bold break-words">{player.name}</span>
            {player.captain && team !== 0 && (
              <span className="inline-flex items-center gap-1 text-sm font-bold text-gold"><Icon name="star" /> Capitão do time</span>
            )}
          </span>
          {mine && (
            <Button variant="ghost" disabled={action.busy} onClick={() => change(() => sendJson<LobbyView>("POST", "/lobby/leave"))}>Sair</Button>
          )}
          {me.is_admin && !mine && (
            <Button variant="danger" disabled={action.busy} aria-label={`Remover ${player.name}`} onClick={() => change(() => sendJson<LobbyView>("DELETE", `/lobby/players/${player.id}`))}>
              <Icon name="x" />
            </Button>
          )}
        </li>
      );
    }
    const label = team === 0 ? "Vazio" : slot === 0 ? "Vazio (capitão)" : "Vazio";
    const inner = (
      <>
        <span aria-hidden="true" className="grid size-10 place-items-center rounded-full bg-surface-3 text-xl text-muted">+</span>
        <span className="flex-1 text-lg font-bold text-muted">{label}</span>
      </>
    );
    return (
      <li key={slot}>
        {canJoin ? (
          <button
            type="button"
            disabled={action.busy}
            aria-label={`Entrar no ${team === 0 ? "espectador" : `time ${team}`}`}
            onClick={() => change(() => sendJson<LobbyView>("POST", "/lobby/join", { team }))}
            className={clsx("flex w-full items-center gap-3 rounded-xl border border-line-soft bg-surface-2 px-3 text-left transition hover:border-accent hover:bg-surface-3 disabled:opacity-60", compact ? "min-h-14" : "min-h-16")}
          >
            {inner}
          </button>
        ) : (
          <div className={clsx("flex items-center gap-3 rounded-xl border border-line-soft bg-surface-2 px-3", compact ? "min-h-14" : "min-h-16")}>{inner}</div>
        )}
      </li>
    );
  }

  function teamColumn(id: 1 | 2) {
    const team = v.teams.find((t) => t.id === id);
    if (!team) return null;
    return (
      <section aria-labelledby={`time-${id}`} className={clsx("flex flex-col gap-2", id === 1 ? "lg:order-1" : "lg:order-3")}>
        <div className={clsx("flex items-center justify-between rounded-xl border border-line-soft border-t-4 bg-surface-2 px-4 py-3", id === 1 ? "border-t-pt" : "border-t-pl")}>
          <h2 id={`time-${id}`} className="text-2xl font-bold">Time {id}</h2>
          <span className="num text-xl text-muted">{team.players.length}/{v.team_size}</span>
        </div>
        <ul className="flex flex-col gap-2">
          {Array.from({ length: v.team_size }, (_, slot) => row(team.players[slot], id, slot))}
        </ul>
      </section>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted" role="status">
          {failed ? "Sem conexão com a liga. Tentando de novo..." : "Atualiza sozinho a cada poucos segundos."}
        </p>
        {!loggedIn && <SteamLogin />}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_1.4fr_1fr]">
        <section aria-labelledby="lobby-centro" className="flex flex-col gap-3 lg:order-2">
          <div className="flex flex-col items-center gap-3 rounded-xl border border-line bg-surface-2 p-5 text-center">
            <span className="self-start rounded-md bg-surface-3 px-2.5 py-1 text-sm font-bold">{mapName}{view.format !== "md1" ? ` • ${FORMAT_LABEL[view.format]}` : ""}</span>
            <h2 id="lobby-centro" className="sr-only">Partida</h2>
            <p aria-hidden="true" className="num text-6xl leading-none">0 : 0</p>
            <p className="rounded-full bg-surface-3 px-3 py-1 text-base text-muted" role="status">
              {view.ready ? "Times completos" : "Aguardando jogadores"} <span className="num font-bold text-fg">{view.count} / {view.team_size * 2}</span>
            </p>
            <Button variant="gold" disabled={!view.ready || !me.can_get_json || action.busy} onClick={start}>Iniciar partida</Button>
            {!view.ready && <p className="text-sm text-muted">Libera com 5 contra 5.</p>}
            {view.ready && !me.can_get_json && <p className="text-sm text-muted">Só quem está no lobby recebe o arquivo da partida.</p>}
          </div>

          <div className="rounded-xl border border-line-soft bg-surface-2 p-4">
            <h3 className="text-lg font-bold">Configurar lobby</h3>
            <p className="mb-3 text-sm text-muted">
              {me.can_configure ? "Você é capitão: escolha o formato e o mapa." : "Só os capitães (e o admin) mudam o formato e o mapa."}
            </p>
            <div className="flex items-center justify-between gap-3 border-t border-line-soft py-3">
              <span className="text-lg font-bold">Formato</span>
              <div role="radiogroup" aria-label="Formato da partida" className="flex gap-2">
                {view.formats.map((f) => (
                  <Button key={f.id} role="radio" aria-checked={view.format === f.id} variant={view.format === f.id ? "gold" : "secondary"}
                    disabled={!me.can_configure || action.busy}
                    onClick={() => change(() => sendJson<LobbyView>("PATCH", "/lobby", { format: f.id }))}>
                    {FORMAT_LABEL[f.id]}
                  </Button>
                ))}
              </div>
            </div>
            <div className="flex items-center justify-between gap-3 border-t border-line-soft py-3">
              <span className="text-lg font-bold">{view.format === "md1" ? "Mapa" : "Mapa 1"}: {mapName}</span>
              <Button variant="secondary" aria-expanded={showMaps} onClick={() => setShowMaps((v) => !v)}>Mapas</Button>
            </div>
            {showMaps && (
              <div role="radiogroup" aria-label="Mapa" className="flex flex-wrap gap-2 border-t border-line-soft pt-3">
                {view.maps.map((m) => (
                  <Button key={m.id} role="radio" aria-checked={view.map === m.id} variant={view.map === m.id ? "gold" : "secondary"}
                    disabled={!me.can_configure || action.busy}
                    onClick={() => change(() => sendJson<LobbyView>("PATCH", "/lobby", { map: m.id }))}>
                    {m.name}
                  </Button>
                ))}
              </div>
            )}
            {view.format !== "md1" && (
              <p className="border-t border-line-soft pt-3 text-sm text-muted">O restante dos mapas sai do veto no servidor.</p>
            )}
            {me.is_admin && (
              <div className="border-t border-line-soft pt-3">
                {confirmReset ? (
                  <Button variant="danger" disabled={action.busy} onClick={() => { setConfirmReset(false); void change(() => sendJson<LobbyView>("DELETE", "/lobby")); }}>Confirmar: esvaziar lobby</Button>
                ) : (
                  <Button variant="ghost" onClick={() => setConfirmReset(true)}>Esvaziar lobby</Button>
                )}
              </div>
            )}
          </div>
          <Feedback error={action.error} ok={action.ok} />
        </section>
        {teamColumn(1)}
        {teamColumn(2)}
      </div>

      <section aria-labelledby="espectadores" className="flex flex-col gap-2 border-t border-line-soft pt-4">
        <div className="flex items-center justify-between">
          <h2 id="espectadores" className="text-2xl font-bold">Espectadores</h2>
          <span className="num text-lg text-muted">{view.spectators.players.length}/{view.spectators.slots}</span>
        </div>
        <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: view.spectators.slots }, (_, slot) => row(view.spectators.players[slot], 0, slot, true))}
        </ul>
      </section>

      {match && (
        <Card aria-labelledby="lobby-json" className="flex flex-col gap-3">
          <h2 id="lobby-json" className="text-2xl font-bold">Arquivo da partida</h2>
          <ol className="max-w-prose list-decimal space-y-1.5 pl-6 text-base text-muted">
            <li>Salve o texto abaixo como <code>edb.json</code> na pasta <code>cfg</code> do servidor.</li>
            <li>No console do servidor (ou como admin), digite <code>matchzy_loadmatch edb.json</code>.</li>
            <li>Todos entram no servidor: o MatchZy leva cada jogador direto para o seu time (espectadores vão para o espectador). Depois é só usar <code>.ready</code>.</li>
          </ol>
          <pre className="max-h-72 overflow-auto rounded-lg border border-line bg-surface p-3 text-sm">{match.json}</pre>
          <div><Button variant="secondary" onClick={() => copy(match.json)}>{copied ? "Copiado" : "Copiar JSON"}</Button></div>
        </Card>
      )}
    </div>
  );
}
