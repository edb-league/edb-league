"use client";

import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { CheckboxField, SelectField, TextField } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { getJson, sendJson } from "@/lib/client";
import type { AdminOverview, ConfrontCandidates, ConfrontRequest } from "@/lib/types";
import { Feedback, useAction } from "./useAction";

type Format = "bo1" | "bo3";

export function ConfrontTab({ overview, onChanged }: { overview: AdminOverview; onChanged: () => void }) {
  const seasons = [...overview.open_seasons].sort((a, b) => b.number - a.number);
  const [season, setSeason] = useState(String(seasons[0]?.number ?? ""));
  const [format, setFormat] = useState<Format>("bo3");
  const [cand, setCand] = useState<ConfrontCandidates | null>(null);
  const [chosen, setChosen] = useState<string[]>([]);
  const [teamA, setTeamA] = useState<string[]>([]);
  const [nameA, setNameA] = useState("PT");
  const [nameB, setNameB] = useState("PL");
  const [scores, setScores] = useState<Record<string, [string, string]>>({});
  const [confirmed, setConfirmed] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const submit = useAction();
  const total = format === "bo1" ? 1 : 3;

  useEffect(() => {
    if (!overview.cloud || !season) return;
    let cancelled = false;
    getJson<ConfrontCandidates>(`/admin/confront/candidates?season=${encodeURIComponent(season)}`)
      .then((data) => {
        if (cancelled) return;
        setCand(data);
        setLoadError(null);
      })
      .catch((e: unknown) => {
        if (!cancelled) setLoadError(e instanceof Error ? e.message : "Não foi possível carregar os mapas.");
      });
    return () => {
      cancelled = true;
    };
  }, [season, overview.cloud, version]);

  const playerName = useMemo(() => new Map((cand?.players ?? []).map((p) => [p.id, p.name])), [cand]);
  const mapById = useMemo(() => new Map((cand?.maps ?? []).map((m) => [m.id, m])), [cand]);
  const roster = chosen[0] ? (mapById.get(chosen[0])?.player_ids ?? []) : [];

  function clearSelection() {
    setChosen([]);
    setTeamA([]);
    setScores({});
    setConfirmed(false);
  }

  function resetSelection() {
    clearSelection();
    submit.reset();
  }

  if (!overview.cloud) {
    return (
      <Card>
        <h3 className="mb-2 text-xl font-bold">Registrar confronto BO1 ou BO3</h3>
        <Notice tone="info">O registro oficial de confrontos exige o banco online (Supabase).</Notice>
      </Card>
    );
  }
  if (seasons.length === 0) {
    return (
      <Card>
        <h3 className="mb-2 text-xl font-bold">Registrar confronto BO1 ou BO3</h3>
        <Notice tone="info">Não há temporadas abertas para registrar confrontos.</Notice>
      </Card>
    );
  }

  const ready = chosen.length === total && roster.length === 10 && teamA.length === 5;

  return (
    <Card aria-labelledby="confronto-titulo">
      <h3 id="confronto-titulo" className="text-xl font-bold">Registrar confronto BO1 ou BO3</h3>
      <p className="mb-4 max-w-prose text-base text-muted">
        Primeiro importe os mapas com seus dados na aba Importar. Aqui você escolhe 1 mapa (BO1) ou 3 mapas (BO3),
        informa os placares e confirma os dois times. Cada mapa conta igualmente nos rankings.
      </p>

      <form
        className="flex flex-col gap-6"
        onSubmit={async (event) => {
          event.preventDefault();
          const body: ConfrontRequest = {
            season: Number(season),
            format,
            match_ids: chosen,
            team_a_ids: teamA,
            scores: Object.fromEntries(chosen.map((id) => [id, [Number(scores[id]?.[0] ?? 0), Number(scores[id]?.[1] ?? 0)] as [number, number]])),
            team_a_name: nameA,
            team_b_name: nameB,
          };
          const done = await submit.run(
            () => sendJson<{ ok: boolean }>("POST", "/admin/confront", body),
            `${format.toUpperCase()} registrada. Os rankings foram atualizados.`,
          );
          if (done) {
            clearSelection();
            setVersion((v) => v + 1);
            onChanged();
          }
        }}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <SelectField
            id="conf-temporada"
            label="Temporada"
            value={season}
            onChange={(e) => {
              setSeason(e.target.value);
              setCand(null);
              resetSelection();
            }}
          >
            {seasons.map((s) => (
              <option key={s.number} value={s.number}>
                {s.label}
              </option>
            ))}
          </SelectField>
          <fieldset>
            <legend className="mb-1.5 text-base font-bold">Formato da partida</legend>
            <div className="flex gap-3">
              {(["bo1", "bo3"] as const).map((f) => (
                <label key={f} className="flex min-h-11 flex-1 cursor-pointer press items-center gap-3 rounded-lg border border-line bg-surface px-4 has-[:checked]:border-accent has-[:checked]:bg-surface-2">
                  <input
                    type="radio"
                    name="formato"
                    value={f}
                    checked={format === f}
                    className="size-5"
                    onChange={() => {
                      setFormat(f);
                      resetSelection();
                    }}
                  />
                  <span className="text-base font-bold">{f.toUpperCase()}</span>
                </label>
              ))}
            </div>
          </fieldset>
        </div>

        <fieldset>
          <legend className="mb-1 text-base font-bold">
            Selecione {total} mapa{total > 1 ? "s" : ""}, na ordem em que {total > 1 ? "foram disputados" : "foi disputado"}
          </legend>
          {loadError && <Feedback error={loadError} ok={null} />}
          {cand && cand.maps.length === 0 ? (
            <Notice tone="info">Nenhum mapa avulso disponível nesta temporada. Importe o primeiro mapa.</Notice>
          ) : (
            <ul className="mt-2 grid max-h-72 gap-1 overflow-y-auto rounded-lg border border-line-soft bg-surface p-2 md:grid-cols-2">
              {(cand?.maps ?? []).map((m) => {
                const index = chosen.indexOf(m.id);
                const checked = index >= 0;
                return (
                  <li key={m.id}>
                    <label className="flex min-h-11 cursor-pointer press items-center gap-3 rounded-lg px-3 py-1.5 hover:bg-surface-2 has-[:disabled]:cursor-not-allowed has-[:disabled]:opacity-60">
                      <input
                        type="checkbox"
                        className="size-5"
                        checked={checked}
                        disabled={!checked && chosen.length >= total}
                        onChange={() => {
                          setTeamA([]);
                          setConfirmed(false);
                          setChosen((c) => (c.includes(m.id) ? c.filter((x) => x !== m.id) : [...c, m.id]));
                        }}
                      />
                      <span className="min-w-0 flex-1 text-base break-words">{m.label}</span>
                      {checked && <span className="tabular shrink-0 text-sm font-bold text-accent">Mapa {index + 1}</span>}
                    </label>
                  </li>
                );
              })}
            </ul>
          )}
          <p className="mt-2 text-sm text-muted" aria-live="polite">
            {chosen.length} de {total} selecionado{chosen.length === 1 ? "" : "s"}
          </p>
        </fieldset>

        {chosen.length === total && roster.length !== 10 && (
          <Notice tone="error">O primeiro mapa deve ter 10 jogadores cadastrados, 5 contra 5.</Notice>
        )}

        {chosen.length === total && roster.length === 10 && (
          <>
            <div className="grid gap-4 md:grid-cols-2">
              <TextField id="conf-a" label="Time A (vermelho)" value={nameA} onChange={(e) => setNameA(e.target.value)} />
              <TextField id="conf-b" label="Time B (azul)" value={nameB} onChange={(e) => setNameB(e.target.value)} />
            </div>

            <fieldset>
              <legend className="mb-1 text-base font-bold">Escolha os 5 jogadores do Time A</legend>
              <ul className="mt-2 grid gap-1 rounded-lg border border-line-soft bg-surface p-2 sm:grid-cols-2">
                {roster.map((pid) => {
                  const checked = teamA.includes(pid);
                  return (
                    <li key={pid}>
                      <label className="flex min-h-11 cursor-pointer press items-center gap-3 rounded-lg px-3 py-1.5 hover:bg-surface-2 has-[:disabled]:cursor-not-allowed has-[:disabled]:opacity-60">
                        <input
                          type="checkbox"
                          className="size-5"
                          checked={checked}
                          disabled={!checked && teamA.length >= 5}
                          onChange={() => setTeamA((t) => (t.includes(pid) ? t.filter((x) => x !== pid) : [...t, pid]))}
                        />
                        <span className="text-base break-words">{playerName.get(pid) ?? pid}</span>
                      </label>
                    </li>
                  );
                })}
              </ul>
              {teamA.length === 5 && (
                <p className="mt-2 text-base text-muted">
                  <b className="text-fg">Time B:</b> {roster.filter((p) => !teamA.includes(p)).map((p) => playerName.get(p) ?? p).join(", ")}
                </p>
              )}
            </fieldset>

            <div className="flex flex-col gap-4">
              {chosen.map((id, i) => {
                const m = mapById.get(id);
                const value = scores[id] ?? [String(m?.team_a_score ?? 0), String(m?.team_b_score ?? 0)];
                return (
                  <fieldset key={id} className="rounded-lg border border-line-soft p-4">
                    <legend className="px-2 text-base font-bold">
                      Mapa {i + 1} · {m?.map_name ?? "Mapa"} ({m?.played_at})
                    </legend>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <TextField
                        id={`score-a-${id}`}
                        label={`Rounds do ${nameA || "Time A"}`}
                        type="number"
                        inputMode="numeric"
                        min={0}
                        max={80}
                        value={value[0]}
                        onChange={(e) => setScores((s) => ({ ...s, [id]: [e.target.value, value[1]] }))}
                      />
                      <TextField
                        id={`score-b-${id}`}
                        label={`Rounds do ${nameB || "Time B"}`}
                        type="number"
                        inputMode="numeric"
                        min={0}
                        max={80}
                        value={value[1]}
                        onChange={(e) => setScores((s) => ({ ...s, [id]: [value[0], e.target.value] }))}
                      />
                    </div>
                    {m?.rounds_total ? (
                      <p className="mt-2 text-sm text-muted">Os placares precisam somar {m.rounds_total} rounds.</p>
                    ) : null}
                  </fieldset>
                );
              })}
            </div>

            <CheckboxField
              id="conf-confirma"
              label="Conferi os placares, os 10 jogadores e a divisão das equipes."
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
          </>
        )}

        <Feedback error={submit.error} ok={submit.ok} />
        <div>
          <Button type="submit" disabled={!ready || !confirmed || submit.busy}>
            {submit.busy ? "Registrando..." : `Registrar ${format.toUpperCase()} na temporada`}
          </Button>
        </div>
      </form>
    </Card>
  );
}
