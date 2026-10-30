"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SelectField, TextField } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { sendForm, sendJson } from "@/lib/client";
import type {
  SeriesChoice,
  SeriesCommitResult,
  SeriesItem,
  SeriesMap,
  SeriesPending,
  SeriesPlayer,
  SeriesPreview,
} from "@/lib/types";
import { Feedback, useAction } from "./useAction";

/** "" = sem resposta; "new"; "link:<id>" (jogador sem SteamID); "alias:<id>" (outra conta de quem já tem SteamID). */
type Picks = Record<string, { pick: string; nickname: string }>;

function toChoice(entry: { pick: string; nickname: string } | undefined): SeriesChoice | null {
  if (!entry || !entry.pick) return null;
  if (entry.pick === "new") return entry.nickname.trim() ? { kind: "new", nickname: entry.nickname.trim() } : null;
  const [kind, id] = entry.pick.split(":");
  if (kind === "link" || kind === "alias") return id ? { kind, player_id: id } : null;
  return null;
}

function initialPicks(item: SeriesItem): Picks {
  const picks: Picks = {};
  for (const p of item.unresolved) {
    picks[p.steamid] = { pick: p.suggestion ? `link:${p.suggestion.id}` : "", nickname: p.nick };
  }
  return picks;
}

function TeamRows({ players, name }: { players: SeriesPlayer[]; name: string }) {
  return (
    <>
      <tr>
        <Th colSpan={7} className="bg-surface-2 text-left">
          {name}
        </Th>
      </tr>
      {players.map((p) => (
        <tr key={p.steamid}>
          <Td>
            <span className="font-bold">{p.player ?? p.nick}</span>
            {!p.player && (
              <span className="ml-2">
                <Badge tone="gold">Novo na base</Badge>
              </span>
            )}
          </Td>
          <Td numeric>
            {p.kills}/{p.deaths}/{p.assists}
          </Td>
          <Td numeric>{p.adr.toFixed(1)}</Td>
          <Td numeric>{p.kast}%</Td>
          <Td numeric>{p.headshots}</Td>
          <Td numeric>{p.rating === null ? "—" : p.rating.toFixed(2)}</Td>
        </tr>
      ))}
    </>
  );
}

function MapBlock({ map, teamA, teamB }: { map: SeriesMap; teamA: string; teamB: string }) {
  const winner = map.score_a > map.score_b ? teamA : teamB;
  return (
    <div className="flex flex-col gap-2">
      <h5 className="text-lg font-bold">
        Mapa {map.order} · {map.map}{" "}
        <span className="tabular text-muted">
          {teamA} {map.score_a} x {map.score_b} {teamB}
        </span>{" "}
        <Badge tone="win">{winner} venceu</Badge>
      </h5>
      <p className="text-sm text-muted">
        {map.file} · {map.rounds} rounds
      </p>
      {map.warnings.length > 0 && (
        <Notice tone="warning" title="Avisos da leitura">
          <ul className="list-disc pl-5">
            {map.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </Notice>
      )}
      <TableWrap caption={`Estatísticas do mapa ${map.order}, ${map.map}`}>
        <thead>
          <tr>
            <Th>Jogador</Th>
            <Th numeric>K/D/A</Th>
            <Th numeric>ADR</Th>
            <Th numeric>KAST</Th>
            <Th numeric>HS</Th>
            <Th numeric>Rating*</Th>
          </tr>
        </thead>
        <tbody>
          <TeamRows name={teamA} players={map.players.filter((p) => p.team === "A")} />
          <TeamRows name={teamB} players={map.players.filter((p) => p.team === "B")} />
        </tbody>
      </TableWrap>
    </div>
  );
}

function Identity({
  item,
  options,
  picks,
  setPicks,
}: {
  item: SeriesPending;
  options: SeriesPreview["players"];
  picks: Picks;
  setPicks: (next: Picks) => void;
}) {
  const entry = picks[item.steamid] ?? { pick: "", nickname: item.nick };
  const free = options.filter((o) => !o.has_steamid);
  const registered = options.filter((o) => o.has_steamid);
  const update = (change: Partial<typeof entry>) => setPicks({ ...picks, [item.steamid]: { ...entry, ...change } });
  return (
    <li className="grid gap-3 rounded-lg border border-line-soft bg-surface p-3 md:grid-cols-2">
      <SelectField
        id={`id-${item.steamid}`}
        label={`Quem é ${item.nick || "este jogador"}?`}
        hint={`SteamID ${item.steamid}`}
        value={entry.pick}
        onChange={(e) => update({ pick: e.target.value })}
      >
        <option value="">Escolha…</option>
        <option value="new">Criar jogador novo</option>
        <optgroup label="Vincular a jogador sem SteamID">
          {free.map((o) => (
            <option key={o.id} value={`link:${o.id}`}>
              {o.nickname}
            </option>
          ))}
        </optgroup>
        <optgroup label="É outra conta de um jogador já cadastrado">
          {registered.map((o) => (
            <option key={o.id} value={`alias:${o.id}`}>
              {o.nickname}
            </option>
          ))}
        </optgroup>
      </SelectField>
      {entry.pick === "new" && (
        <TextField
          id={`nick-${item.steamid}`}
          label="Nickname do novo jogador"
          value={entry.nickname}
          maxLength={60}
          onChange={(e) => update({ nickname: e.target.value })}
        />
      )}
    </li>
  );
}

function SeriesCard({
  item,
  data,
  swap,
  onDone,
}: {
  item: SeriesItem;
  data: SeriesPreview;
  swap: boolean;
  onDone: (key: string) => void;
}) {
  const [picks, setPicks] = useState<Picks>(() => initialPicks(item));
  const save = useAction();
  const answered = item.unresolved.every((p) => toChoice(picks[p.steamid]));
  const blocked = !item.can_commit || !answered || save.busy;

  async function commit() {
    const choices: Record<string, SeriesChoice> = {};
    for (const p of item.unresolved) {
      const choice = toChoice(picks[p.steamid]);
      if (choice) choices[p.steamid] = choice;
    }
    const done = await save.run(() =>
      sendJson<SeriesCommitResult>("POST", "/admin/import/series/commit", {
        payload: item.payload,
        team_a: data.team_a,
        team_b: data.team_b,
        swap,
        choices,
      }),
    );
    if (done) onDone(item.key);
  }

  return (
    <Card aria-labelledby={`serie-${item.key}`}>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h4 id={`serie-${item.key}`} className="text-xl font-bold">
          {item.label}
        </h4>
        {item.season !== null && <Badge tone="accent">Temporada {item.season}</Badge>}
        <Badge>{item.format === "bo3" ? "Melhor de 3" : "Melhor de 1"}</Badge>
      </div>
      {item.basis && (
        <p className="mb-3 text-base text-muted">
          {data.team_a} = {item.basis}.
        </p>
      )}
      {item.problems.length > 0 && (
        <Notice tone="error" title="Esta série não pode ser gravada" className="mb-4">
          <ul className="list-disc pl-5">
            {item.problems.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </Notice>
      )}
      {(item.notes.length > 0 || item.changes.length > 0) && (
        <Notice tone="warning" title="Confira" className="mb-4">
          <ul className="list-disc pl-5">
            {[...item.notes, ...item.changes].map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </Notice>
      )}

      <div className="flex flex-col gap-6">
        {item.maps.map((map) => (
          <MapBlock key={map.file} map={map} teamA={data.team_a} teamB={data.team_b} />
        ))}
      </div>
      {item.maps.length > 0 && (
        <p className="mt-2 text-sm text-muted">
          *Rating 2.0 estimado a partir da demo (fórmula pública da HLTV); não é o do SCOPE.
        </p>
      )}

      {item.unresolved.length > 0 && (
        <section className="mt-6" aria-labelledby={`pend-${item.key}`}>
          <h5 id={`pend-${item.key}`} className="text-lg font-bold">
            Contas que ainda não estão cadastradas
          </h5>
          <p className="mb-3 text-base text-muted">
            Diga quem é cada uma. A conta fica ligada ao jogador e é reconhecida sozinha nas próximas demos.
          </p>
          <ul className="flex flex-col gap-3">
            {item.unresolved.map((p) => (
              <Identity key={p.steamid} item={p} options={data.players} picks={picks} setPicks={setPicks} />
            ))}
          </ul>
          <Button
            variant="ghost"
            className="mt-3"
            onClick={() => {
              const next = { ...picks };
              for (const p of item.unresolved) {
                if (!toChoice(next[p.steamid])) next[p.steamid] = { pick: "new", nickname: p.nick };
              }
              setPicks(next);
            }}
          >
            Criar como novos os que faltam
          </Button>
        </section>
      )}

      <div className="mt-6 flex flex-col gap-3">
        <Feedback error={save.error} ok={null} />
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="gold" disabled={blocked} onClick={commit}>
            {save.busy ? "Gravando..." : "Gravar série"}
          </Button>
          {item.can_commit && !answered && (
            <span className="text-sm text-muted">Responda quem é cada conta cadastrada acima para gravar.</span>
          )}
        </div>
      </div>
    </Card>
  );
}

export function SeriesImportTab({ onChanged }: { onChanged: () => void }) {
  const [files, setFiles] = useState<File[]>([]);
  const [fileKey, setFileKey] = useState(0);
  const [teamA, setTeamA] = useState("PT");
  const [teamB, setTeamB] = useState("PL");
  const [swap, setSwap] = useState(false);
  const [data, setData] = useState<SeriesPreview | null>(null);
  const [usedSwap, setUsedSwap] = useState(false);
  const [saved, setSaved] = useState<string[]>([]);
  const read = useAction();

  function discard() {
    setData(null);
    setFiles([]);
    setFileKey((k) => k + 1);
    read.reset();
  }

  return (
    <div className="flex flex-col gap-6">
      <Card aria-labelledby="serie-titulo">
        <h3 id="serie-titulo" className="text-xl font-bold">Importar série (md1 ou md3)</h3>
        <p className="mb-4 max-w-prose text-base text-muted">
          Envie as demos da série de uma vez. O nome do arquivo traz o formato, o mapa, a data e a ordem
          (<span className="font-mono">md3_inferno_20_10_1.dem</span>). O site separa os times, confere o placar e
          mostra tudo antes de gravar.
        </p>
        <Notice tone="info" title="Dica: analise no seu computador" className="mb-4">
          Uma demo tem cerca de 230 MB e a leitura leva minutos. Rode{" "}
          <span className="font-mono">python scripts/edb_import.py --painel</span> e envie aqui os arquivos{" "}
          <span className="font-mono">.edb.json</span> da pasta <span className="font-mono">para_o_painel</span>:
          são poucos KB e a prévia sai na hora.
        </Notice>
        <form
          className="flex flex-col gap-5"
          onSubmit={async (event) => {
            event.preventDefault();
            const form = new FormData();
            for (const f of files) form.append("files", f);
            form.set("team_a", teamA.trim() || "PT");
            form.set("team_b", teamB.trim() || "PL");
            form.set("swap", swap ? "true" : "false");
            setSaved([]);
            const result = await read.run(() => sendForm<SeriesPreview>("/admin/import/series/preview", form));
            if (result) {
              setData(result);
              setUsedSwap(swap);
            }
          }}
        >
          <div className="flex flex-col gap-1.5">
            <label htmlFor="serie-arquivos" className="text-base font-bold">
              Arquivos da série
            </label>
            <input
              key={fileKey}
              id="serie-arquivos"
              type="file"
              multiple
              required
              accept=".dem,.gz,.json"
              className="min-h-11 w-full rounded-lg border border-line bg-surface px-3 py-2 text-base file:mr-3 file:min-h-9 file:rounded-md file:border-0 file:bg-surface-3 file:px-3 file:font-bold file:text-fg"
              onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
            />
            {files.length > 0 && <p className="text-sm text-muted">{files.length} arquivo(s) escolhido(s).</p>}
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <TextField id="serie-time-a" label="Time A" value={teamA} maxLength={30} onChange={(e) => setTeamA(e.target.value)} />
            <TextField id="serie-time-b" label="Time B" value={teamB} maxLength={30} onChange={(e) => setTeamB(e.target.value)} />
            <label className="flex min-h-11 cursor-pointer items-center gap-3 self-end text-base">
              <input type="checkbox" className="size-6" checked={swap} onChange={(e) => setSwap(e.target.checked)} />
              Inverter os times
            </label>
          </div>
          <Feedback error={read.error} ok={null} />
          <div className="flex flex-wrap gap-3">
            <Button type="submit" disabled={read.busy || files.length === 0}>
              {read.busy ? "Lendo..." : "Ler série"}
            </Button>
            {data && (
              <Button variant="ghost" onClick={discard}>
                Descartar leitura
              </Button>
            )}
          </div>
        </form>
      </Card>

      {saved.length > 0 && (
        <Notice tone="success">Série gravada: {saved.join(", ")}. As estatísticas já entram nos rankings.</Notice>
      )}

      {data && data.notes.length > 0 && (
        <Notice tone="warning" title="Arquivos ignorados ou já importados">
          <ul className="list-disc pl-5">
            {data.notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </Notice>
      )}

      {data && data.series.length === 0 && (
        <Notice tone="info">Nenhuma série nova para gravar com esses arquivos.</Notice>
      )}

      {data?.series.map((item) => (
        <SeriesCard
          key={item.key}
          item={item}
          data={data}
          swap={usedSwap}
          onDone={(key) => {
            setSaved((s) => [...s, item.label]);
            setData((d) => (d ? { ...d, series: d.series.filter((x) => x.key !== key) } : d));
            onChanged();
          }}
        />
      ))}
    </div>
  );
}
