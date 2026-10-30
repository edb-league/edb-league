"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { TextField } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { TableWrap, Td, Th } from "@/components/ui/Table";
import { sendForm, sendJson } from "@/lib/client";
import type { ImportCommit, ImportPlayer, ImportPreview } from "@/lib/types";
import { Feedback, useAction } from "./useAction";

type Method = "demo" | "csv" | "sample";

const METHODS: { value: Method; label: string; hint: string }[] = [
  { value: "demo", label: "Arquivo de demo (.dem ou .gz)", hint: "Lê o replay da partida automaticamente." },
  { value: "csv", label: "Placar em CSV", hint: "Planilha com as estatísticas de cada jogador." },
  { value: "sample", label: "Exemplo da liga", hint: "Carrega um placar de teste, sem enviar arquivo." },
];

const NUMERIC: { key: keyof ImportPlayer; label: string }[] = [
  { key: "kills", label: "Kills" },
  { key: "deaths", label: "Mortes" },
  { key: "assists", label: "Assist." },
  { key: "damage", label: "Dano" },
  { key: "rounds", label: "Rounds" },
  { key: "headshots", label: "HS" },
];

function todayInSaoPaulo() {
  return new Date().toLocaleDateString("en-CA", { timeZone: "America/Sao_Paulo" });
}

function toNumber(value: string) {
  const n = Number(value);
  return Number.isFinite(n) && n >= 0 ? n : 0;
}

export function ImportTab({ onChanged }: { onChanged: () => void }) {
  const [method, setMethod] = useState<Method>("demo");
  const [file, setFile] = useState<File | null>(null);
  const [fileKey, setFileKey] = useState(0);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [players, setPlayers] = useState<ImportPlayer[]>([]);
  const [winners, setWinners] = useState<string[]>([]);
  const [playedAt, setPlayedAt] = useState(todayInSaoPaulo);
  const [mapName, setMapName] = useState("");
  const [rounds, setRounds] = useState("0");
  const [note, setNote] = useState("");
  const read = useAction();
  const save = useAction();

  const needsFile = method !== "sample";
  const blocked = Boolean(preview?.duplicate || preview?.invalid_stats);
  const nicknames = useMemo(() => players.map((p) => p.nickname), [players]);

  function discard() {
    setPreview(null);
    setPlayers([]);
    setWinners([]);
    setNote("");
    setFile(null);
    setFileKey((k) => k + 1);
    read.reset();
  }

  function patch(index: number, change: Partial<ImportPlayer>) {
    setPlayers((list) => list.map((p, i) => (i === index ? { ...p, ...change } : p)));
  }

  return (
    <div className="flex flex-col gap-6">
      <Card aria-labelledby="importar-titulo">
        <h3 id="importar-titulo" className="text-xl font-bold">Importar partida</h3>
        <p className="mb-4 max-w-prose text-base text-muted">
          Leia uma demo ou um placar, confira os números na tabela e só então grave a partida. Nada é salvo antes da
          sua confirmação.
        </p>
        <form
          className="flex flex-col gap-5"
          onSubmit={async (event) => {
            event.preventDefault();
            const form = new FormData();
            form.set("method", method);
            if (needsFile && file) form.set("file", file);
            save.reset();
            const data = await read.run(() => sendForm<ImportPreview>("/admin/import/preview", form));
            if (data) {
              setPreview(data);
              setPlayers(data.players);
              setWinners(data.players.filter((p) => p.won === true).map((p) => p.nickname));
              setMapName(data.map);
              setRounds(String(data.rounds_total));
              if (data.played_at) setPlayedAt(data.played_at);
            }
          }}
        >
          <fieldset>
            <legend className="mb-2 text-base font-bold">Origem dos dados</legend>
            <div className="grid gap-2 md:grid-cols-3">
              {METHODS.map((m) => (
                <label
                  key={m.value}
                  className="flex min-h-11 cursor-pointer press items-start gap-3 rounded-lg border border-line bg-surface p-3 has-[:checked]:border-accent has-[:checked]:bg-surface-2"
                >
                  <input
                    type="radio"
                    name="origem"
                    value={m.value}
                    checked={method === m.value}
                    className="mt-1 size-5 shrink-0"
                    onChange={() => {
                      setMethod(m.value);
                      setFile(null);
                      setFileKey((k) => k + 1);
                    }}
                  />
                  <span>
                    <span className="block text-base font-bold">{m.label}</span>
                    <span className="block text-sm text-muted">{m.hint}</span>
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          {needsFile && (
            <div className="flex flex-col gap-1.5">
              <label htmlFor="import-arquivo" className="text-base font-bold">
                {method === "demo" ? "Arquivo .dem" : "Arquivo .csv"}
              </label>
              <input
                key={fileKey}
                id="import-arquivo"
                type="file"
                accept={method === "demo" ? ".dem,.gz" : ".csv,text/csv"}
                required
                className="min-h-11 w-full rounded-lg border border-line bg-surface px-3 py-2 text-base file:mr-3 file:min-h-9 file:rounded-md file:border-0 file:bg-surface-3 file:px-3 file:font-bold file:text-fg"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </div>
          )}

          <Feedback error={read.error} ok={null} />
          <div className="flex flex-wrap gap-3">
            <Button type="submit" disabled={read.busy || (needsFile && !file)}>
              {read.busy ? "Lendo..." : "Ler partida"}
            </Button>
            {preview && (
              <Button variant="ghost" onClick={discard}>
                Descartar leitura
              </Button>
            )}
          </div>
        </form>
      </Card>

      {preview && (
        <Card aria-labelledby="conferir-titulo">
          <h3 id="conferir-titulo" className="text-xl font-bold">Conferir e gravar</h3>
          <p className="mb-4 text-base text-muted">
            Fonte: {preview.source}. {players.length} jogadores lidos.
          </p>

          {preview.duplicate && (
            <Notice tone="error" title="Partida já importada" className="mb-4">
              Esta partida já existe no banco. Importar de novo duplicaria as estatísticas, por isso a gravação está
              bloqueada.
            </Notice>
          )}
          {preview.invalid_stats && (
            <Notice tone="error" title="Leitura inválida" className="mb-4">
              A demo veio com 0 kills e 0 mortes para todos. Tente outro arquivo ou use o placar em CSV.
            </Notice>
          )}
          {preview.warnings.length > 0 && (
            <Notice tone="warning" title="Avisos da leitura" className="mb-4">
              <ul className="list-disc pl-5">
                {preview.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            </Notice>
          )}

          <form
            className="flex flex-col gap-6"
            onSubmit={async (event) => {
              event.preventDefault();
              const body: ImportCommit = {
                fingerprint: preview.fingerprint,
                source: preview.source,
                played_at: playedAt,
                map_name: mapName.trim(),
                rounds_total: toNumber(rounds),
                note: note.trim(),
                players,
                winners: winners.filter((w) => nicknames.includes(w)),
              };
              const done = await save.run(
                () => sendJson<{ ok: boolean; match_id?: string }>("POST", "/admin/import/commit", body),
                "Partida gravada. As estatísticas já entram nos rankings.",
              );
              if (done) {
                discard();
                onChanged();
              }
            }}
          >
            <div className="grid gap-4 md:grid-cols-3">
              <TextField id="imp-data" label="Data da partida" type="date" required value={playedAt} onChange={(e) => setPlayedAt(e.target.value)} />
              <TextField id="imp-mapa" label="Mapa" required value={mapName} onChange={(e) => setMapName(e.target.value)} />
              <TextField
                id="imp-rounds"
                label="Total de rounds"
                type="number"
                inputMode="numeric"
                min={1}
                max={80}
                required
                value={rounds}
                onChange={(e) => setRounds(e.target.value)}
              />
            </div>

            <TableWrap caption="Estatísticas lidas por jogador. Todos os campos são editáveis.">
              <thead>
                <tr>
                  <Th>Jogador</Th>
                  {NUMERIC.map((c) => (
                    <Th key={c.key} numeric>
                      {c.label}
                    </Th>
                  ))}
                  <Th>Venceu</Th>
                </tr>
              </thead>
              <tbody>
                {players.map((p, i) => (
                  <tr key={`${p.nickname}-${i}`}>
                    <Td>
                      <input
                        aria-label={`Nickname do jogador ${i + 1}`}
                        className="min-h-11 w-36 rounded-lg border border-line bg-surface px-2 text-base"
                        value={p.nickname}
                        onChange={(e) => {
                          const next = e.target.value;
                          setWinners((w) => w.map((n) => (n === p.nickname ? next : n)));
                          patch(i, { nickname: next });
                        }}
                      />
                    </Td>
                    {NUMERIC.map((c) => (
                      <Td key={c.key} numeric>
                        <input
                          aria-label={`${c.label} de ${p.nickname || `jogador ${i + 1}`}`}
                          type="number"
                          inputMode="numeric"
                          min={0}
                          className="tabular min-h-11 w-20 rounded-lg border border-line bg-surface px-2 text-right text-base"
                          value={(p[c.key] as number | null) ?? 0}
                          onChange={(e) => patch(i, { [c.key]: toNumber(e.target.value) } as Partial<ImportPlayer>)}
                        />
                      </Td>
                    ))}
                    <Td>
                      <input
                        type="checkbox"
                        aria-label={`${p.nickname || `Jogador ${i + 1}`} venceu`}
                        className="size-6"
                        checked={winners.includes(p.nickname)}
                        onChange={(e) =>
                          setWinners((w) => (e.target.checked ? [...w, p.nickname] : w.filter((n) => n !== p.nickname)))
                        }
                      />
                    </Td>
                  </tr>
                ))}
              </tbody>
            </TableWrap>
            <p className="-mt-3 text-sm text-muted">
              Marque quem venceu a partida. Deixe todos desmarcados se o resultado não for informado.
            </p>

            <TextField id="imp-nota" label="Observação (opcional)" value={note} onChange={(e) => setNote(e.target.value)} />

            <Feedback error={save.error} ok={null} />
            <div>
              <Button type="submit" disabled={blocked || save.busy || players.length === 0 || !mapName.trim()}>
                {save.busy ? "Gravando..." : "Gravar partida"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {!preview && save.ok && <Feedback error={null} ok={save.ok} />}
    </div>
  );
}
