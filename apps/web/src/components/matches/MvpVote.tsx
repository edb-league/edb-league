"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, SectionTitle } from "@/components/ui/Card";
import { SelectField } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { getJson, sendJson } from "@/lib/client";
import { dateBR, plural } from "@/lib/format";
import type { MatchMvp } from "@/lib/types";
import { SteamLogin } from "@/components/layout/UserMenu";

/**
 * Votação de MVP do mapa. Fica no navegador porque depende de quem está logado (a página da partida é igual para
 * todos). Sem o recurso ativado no banco, não mostra nada.
 */
export function MvpVote({ matchId }: { matchId: string }) {
  const [data, setData] = useState<MatchMvp | null>(null);
  const [choice, setChoice] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let alive = true;
    getJson<MatchMvp>(`/votes/mvp/${encodeURIComponent(matchId)}`)
      .then((d) => {
        if (!alive) return;
        setData(d);
        setChoice(d.viewer.my_vote ?? "");
      })
      .catch(() => alive && setData(null));
    return () => {
      alive = false;
    };
  }, [matchId]);

  if (!data || data.status === "unavailable") return null;
  const { viewer } = data;

  async function submit() {
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      const next = await sendJson<MatchMvp>("POST", `/votes/mvp/${encodeURIComponent(matchId)}`, { player_id: choice });
      setData(next);
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível registrar o voto.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card aria-labelledby="mvp-titulo">
      <SectionTitle id="mvp-titulo" title="MVP da partida">
        Quem jogou este mapa vota no melhor da partida. É um reconhecimento: não muda rankings, XP nem títulos.
      </SectionTitle>

      {data.status === "open" ? (
        <div className="flex flex-col gap-3">
          <p className="text-base text-muted">
            Votação aberta até {dateBR(data.closes_on)}, ou até todos votarem. {plural(data.votes_cast, "voto", "votos")} de {data.electorate}. O resultado
            aparece quando a votação fecha, e ninguém vê quem votou em quem.
          </p>
          {viewer.can_vote ? (
            <form
              className="flex flex-wrap items-end gap-3"
              onSubmit={(event) => {
                event.preventDefault();
                void submit();
              }}
            >
              <SelectField id="mvp-voto" label="Seu voto" value={choice} onChange={(e) => setChoice(e.target.value)} className="min-w-64">
                <option value="">Escolha um jogador</option>
                {data.candidates.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </SelectField>
              <Button type="submit" disabled={busy || !choice || choice === viewer.my_vote}>
                {busy ? "Enviando..." : viewer.my_vote ? "Trocar voto" : "Votar"}
              </Button>
            </form>
          ) : viewer.logged_in ? (
            <p className="text-base">{viewer.reason}</p>
          ) : (
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-base">{viewer.reason}</p>
              <SteamLogin />
            </div>
          )}
          {viewer.my_vote && !error && <p role="status" className="text-base text-win">{saved ? "Voto registrado. Você pode trocá-lo até a votação fechar." : "Você já votou. Pode trocar o voto até a votação fechar."}</p>}
          {error && <Notice tone="error">{error}</Notice>}
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <p className="text-base text-muted">Votação encerrada com {plural(data.votes_cast, "voto", "votos")}.</p>
          {data.results && data.results.length > 0 ? (
            <ol aria-label="Resultado da votação de MVP" className="flex flex-col gap-2">
              {data.results.map((r) => (
                <li key={r.player.id} className={r.mvp ? "card flex items-baseline justify-between gap-3 border-2 border-gold-bg px-4 py-3" : "card flex items-baseline justify-between gap-3 px-4 py-3"}>
                  <span className="text-lg font-bold">
                    {r.mvp && <span className="mr-2 text-gold">MVP</span>}
                    {r.player.name}
                  </span>
                  <span className="num text-2xl">{plural(r.votes, "voto", "votos")}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-base">Ninguém votou neste mapa.</p>
          )}
        </div>
      )}
    </Card>
  );
}
