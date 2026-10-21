"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { CheckboxField, SelectField, TextField } from "@/components/ui/Field";
import { sendJson } from "@/lib/client";
import type { AdminPlayer } from "@/lib/types";
import { Feedback, useAction } from "./useAction";

const LEVELS = Array.from({ length: 10 }, (_, i) => i + 1);

function RegisterCard({ onChanged }: { onChanged: () => void }) {
  const [nickname, setNickname] = useState("");
  const [steamid, setSteamid] = useState("");
  const [level, setLevel] = useState("5");
  const action = useAction();

  return (
    <Card aria-labelledby="novo-jogador">
      <p className="kicker">Novo jogador</p>
      <h3 id="novo-jogador" className="text-xl font-bold">Cadastrar jogador</h3>
      <p className="mb-4 text-base text-muted">Adicione um atleta ao elenco da liga.</p>
      <form
        className="flex flex-col gap-4"
        onSubmit={async (event) => {
          event.preventDefault();
          const created = await action.run(
            () =>
              sendJson<AdminPlayer>("POST", "/admin/players", {
                nickname,
                steamid: steamid.trim() || null,
                skill_level: Number(level),
              }),
            "Jogador cadastrado.",
          );
          if (created) {
            setNickname("");
            setSteamid("");
            setLevel("5");
            onChanged();
          }
        }}
      >
        <TextField id="novo-nick" label="Nickname" required value={nickname} onChange={(e) => setNickname(e.target.value)} />
        <TextField id="novo-steam" label="SteamID (opcional)" value={steamid} onChange={(e) => setSteamid(e.target.value)} hint="Aceita SteamID64, STEAM_0:Y:Z ou [U:1:N]." />
        <SelectField id="novo-nivel" label="Nível (1 a 10)" value={level} onChange={(e) => setLevel(e.target.value)}>
          {LEVELS.map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </SelectField>
        <Feedback error={action.error} ok={action.ok} />
        <Button type="submit" disabled={action.busy || !nickname.trim()}>
          {action.busy ? "Salvando..." : "Adicionar jogador"}
        </Button>
      </form>
    </Card>
  );
}

/** Formulário de um jogador. É remontado (via key) quando o jogador ou seus dados mudam. */
function PlayerForm({
  player,
  onChanged,
  onArchived,
}: {
  player: AdminPlayer;
  onChanged: () => void;
  onArchived: (message: string) => void;
}) {
  const [level, setLevel] = useState(String(player.level));
  const [nickname, setNickname] = useState(player.nickname);
  const [steamid, setSteamid] = useState(player.steamid ?? "");
  const [confirmArchive, setConfirmArchive] = useState(false);
  const save = useAction();
  const archive = useAction();

  return (
    <div className="flex flex-col gap-6">
      <form
        className="flex flex-col gap-4"
        onSubmit={async (event) => {
          event.preventDefault();
          const done = await save.run(
            () =>
              sendJson<AdminPlayer>("PATCH", `/admin/players/${encodeURIComponent(player.id)}`, {
                nickname,
                steamid: steamid.trim() || null,
                skill_level: Number(level),
              }),
            "Alteração salva.",
          );
          if (done) onChanged();
        }}
      >
        <SelectField id="cfg-nivel" label="Nível (1 a 10)" value={level} onChange={(e) => setLevel(e.target.value)}>
          {LEVELS.map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </SelectField>
        <details className="rounded-lg border border-line-soft p-3">
          <summary className="cursor-pointer text-base font-bold">Editar nickname e SteamID</summary>
          <div className="mt-3 flex flex-col gap-4">
            <TextField id="cfg-nick" label="Nickname" value={nickname} onChange={(e) => setNickname(e.target.value)} />
            <TextField id="cfg-steam" label="SteamID" value={steamid} onChange={(e) => setSteamid(e.target.value)} />
          </div>
        </details>
        <Feedback error={save.error} ok={save.ok} />
        <Button type="submit" variant="secondary" disabled={save.busy}>
          {save.busy ? "Salvando..." : "Salvar alterações"}
        </Button>
      </form>

      <form
        className="flex flex-col gap-3 border-t border-line-soft pt-5"
        onSubmit={async (event) => {
          event.preventDefault();
          if (!confirmArchive) return;
          const done = await archive.run(
            () => sendJson<AdminPlayer>("POST", `/admin/players/${encodeURIComponent(player.id)}/archive`),
          );
          if (done) {
            onArchived(`${player.name} saiu do elenco ativo. O histórico foi preservado.`);
            onChanged();
          }
        }}
      >
        <p className="text-base text-muted">
          Remove o jogador das listas de participantes e do sorteador. O cadastro e o histórico de partidas,
          estatísticas e títulos são preservados. É possível reativá-lo depois.
        </p>
        <CheckboxField
          id="cfg-confirma"
          label="Confirmo que desejo remover este jogador do elenco ativo."
          checked={confirmArchive}
          onChange={(e) => setConfirmArchive(e.target.checked)}
        />
        <Feedback error={archive.error} ok={archive.ok} />
        <Button type="submit" variant="danger" disabled={!confirmArchive || archive.busy}>
          Remover do elenco
        </Button>
      </form>
    </div>
  );
}

function ReactivateForm({ inactive, onChanged }: { inactive: AdminPlayer[]; onChanged: () => void }) {
  const [picked, setPicked] = useState("");
  const reactivate = useAction();
  const reactivateId = inactive.some((p) => p.id === picked) ? picked : (inactive[0]?.id ?? "");

  return (
    <form
      className="mt-3 flex flex-col gap-4"
      onSubmit={async (event) => {
        event.preventDefault();
        const done = await reactivate.run(
          () => sendJson<AdminPlayer>("POST", `/admin/players/${encodeURIComponent(reactivateId)}/reactivate`),
          "Jogador reativado no elenco.",
        );
        if (done) onChanged();
      }}
    >
      <SelectField id="reativar" label="Jogador removido" value={reactivateId} onChange={(e) => setPicked(e.target.value)}>
        {inactive.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </SelectField>
      <Feedback error={reactivate.error} ok={reactivate.ok} />
      <Button type="submit" variant="secondary" disabled={reactivate.busy || !reactivateId}>
        Reativar jogador
      </Button>
    </form>
  );
}

function ConfigCard({ players, onChanged }: { players: AdminPlayer[]; onChanged: () => void }) {
  const byName = (a: AdminPlayer, b: AdminPlayer) => a.name.localeCompare(b.name, "pt-BR");
  const active = useMemo(() => players.filter((p) => p.is_active).sort(byName), [players]);
  const inactive = useMemo(() => players.filter((p) => !p.is_active).sort(byName), [players]);
  const [selectedId, setSelectedId] = useState("");
  const [flash, setFlash] = useState<string | null>(null);
  const selected = active.find((p) => p.id === selectedId) ?? active[0];

  return (
    <Card aria-labelledby="gestao">
      <p className="kicker">Gestão do elenco</p>
      <h3 id="gestao" className="text-xl font-bold">Configurar jogador</h3>
      <p className="mb-4 text-base text-muted">
        Selecione um jogador cadastrado para mudar o nível ou removê-lo do elenco.
      </p>

      {flash && <Feedback error={null} ok={flash} />}
      {!selected ? (
        <p className="mt-2 text-base text-muted">Nenhum jogador ativo para configurar.</p>
      ) : (
        <div className="mt-2 flex flex-col gap-6">
          <SelectField id="cfg-jogador" label="Jogador cadastrado" value={selected.id} onChange={(e) => { setSelectedId(e.target.value); setFlash(null); }}>
            {active.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </SelectField>
          <PlayerForm key={selected.id} player={selected} onChanged={onChanged} onArchived={setFlash} />
        </div>
      )}

      {inactive.length > 0 && (
        <details className="mt-6 rounded-lg border border-line-soft p-3">
          <summary className="cursor-pointer text-base font-bold">Jogadores removidos do elenco ({inactive.length})</summary>
          <ReactivateForm inactive={inactive} onChanged={onChanged} />
        </details>
      )}
    </Card>
  );
}

export function RosterTab({ players, onChanged }: { players: AdminPlayer[]; onChanged: () => void }) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <RegisterCard onChanged={onChanged} />
      <ConfigCard players={players} onChanged={onChanged} />
    </div>
  );
}
