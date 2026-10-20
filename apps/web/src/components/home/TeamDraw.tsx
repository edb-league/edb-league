"use client";

import { useId, useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";
import { TeamTag } from "@/components/ui/Badge";
import { controlClass } from "@/components/ui/Field";
import { sendJson } from "@/lib/client";
import type { DrawPlayer, DrawResult } from "@/lib/types";

const TEAM_SIZE = 10;

function TeamCard({ label, players, total }: { label: "PT" | "PL"; players: DrawPlayer[]; total: number }) {
  return (
    <section aria-label={`Time ${label}`} className="rounded-lg border border-line-soft bg-surface-2 p-4">
      <div className="mb-2 flex items-center justify-between border-b border-line-soft pb-2">
        <TeamTag name={label} />
        <span className="tabular text-base font-bold">{total} pontos</span>
      </div>
      <ul>
        {players.map((p) => (
          <li key={p.id} className="flex items-center justify-between gap-3 py-1.5 text-base">
            <span className="min-w-0 break-words">{p.name}</span>
            <span className="tabular shrink-0 text-muted">Nível {p.level}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** Sorteador 5 contra 5: escolhe 10 presentes e divide em dois times equilibrados pelo nível. */
export function TeamDraw({ roster }: { roster: DrawPlayer[] }) {
  const searchId = useId();
  const [selected, setSelected] = useState<string[]>([]);
  const [filter, setFilter] = useState("");
  const [result, setResult] = useState<DrawResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  const visible = useMemo(() => {
    const term = filter.trim().toLocaleLowerCase("pt-BR");
    return roster.filter((p) => !term || p.name.toLocaleLowerCase("pt-BR").includes(term));
  }, [roster, filter]);

  const full = selected.length >= TEAM_SIZE;

  function toggle(id: string) {
    setResult(null);
    setError(null);
    setSelected((current) => (current.includes(id) ? current.filter((x) => x !== id) : [...current, id]));
  }

  async function draw() {
    setBusy(true);
    setError(null);
    setCopied(false);
    try {
      setResult(await sendJson<DrawResult>("POST", "/draw", { player_ids: selected }));
    } catch (e) {
      setResult(null);
      setError(e instanceof Error ? e.message : "Não foi possível sortear.");
    } finally {
      setBusy(false);
    }
  }

  async function copy() {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.message);
      setCopied(true);
    } catch {
      setError("Não foi possível copiar. Selecione o texto abaixo e copie manualmente.");
    }
  }

  if (roster.length < TEAM_SIZE) {
    return <Notice tone="info">São necessários pelo menos 10 jogadores ativos para sortear os times.</Notice>;
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-base text-muted">
        Selecione exatamente 10 jogadores. O sorteio escolhe, ao acaso, uma das divisões com a menor diferença
        possível na soma dos níveis (1 a 10). Não altera classificações nem registra partidas.
      </p>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={searchId} className="text-base font-bold">
          Buscar jogador
        </label>
        <input
          id={searchId}
          type="search"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Digite parte do nome"
          className={controlClass}
          autoComplete="off"
        />
      </div>

      <fieldset>
        <legend className="mb-2 text-base font-bold">Jogadores presentes</legend>
        <ul className="grid max-h-80 grid-cols-1 gap-1 overflow-y-auto rounded-lg border border-line-soft bg-surface p-2 sm:grid-cols-2">
          {visible.map((p) => {
            const checked = selected.includes(p.id);
            const id = `draw-${p.id}`;
            return (
              <li key={p.id}>
                <label
                  htmlFor={id}
                  className="flex min-h-11 cursor-pointer items-center gap-3 rounded-lg px-3 py-1.5 hover:bg-surface-2 has-[:disabled]:cursor-not-allowed has-[:disabled]:opacity-60"
                >
                  <input
                    id={id}
                    type="checkbox"
                    className="size-5"
                    checked={checked}
                    disabled={!checked && full}
                    onChange={() => toggle(p.id)}
                  />
                  <span className="min-w-0 flex-1 break-words text-base">{p.name}</span>
                  <span className="tabular shrink-0 text-sm text-muted">nível {p.level}</span>
                </label>
              </li>
            );
          })}
          {visible.length === 0 && <li className="px-3 py-2 text-base text-muted">Nenhum jogador encontrado.</li>}
        </ul>
      </fieldset>

      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={draw} disabled={selected.length !== TEAM_SIZE || busy}>
          {busy ? "Sorteando..." : "Sortear times"}
        </Button>
        <Button variant="ghost" onClick={() => { setSelected([]); setResult(null); setError(null); }} disabled={selected.length === 0}>
          Limpar seleção
        </Button>
        <p aria-live="polite" className="tabular text-base text-muted">
          {selected.length} de {TEAM_SIZE} jogadores selecionados
        </p>
      </div>

      {error && <Notice tone="error">{error}</Notice>}

      <div aria-live="polite">
        {result && (
          <div className="flex flex-col gap-4">
            <div className="grid gap-3 md:grid-cols-2">
              <TeamCard label="PT" players={result.team_a} total={result.total_a} />
              <TeamCard label="PL" players={result.team_b} total={result.total_b} />
            </div>
            <p className="text-base text-muted">
              Diferença entre os times: <b className="text-fg">{result.gap}</b> ponto(s) de nível. Sorteie de novo para
              outra combinação equilibrada.
            </p>
            <div>
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <p className="text-base font-bold">Resultado para compartilhar no grupo</p>
                <Button variant="secondary" onClick={copy}>
                  {copied ? "Copiado" : "Copiar texto"}
                </Button>
              </div>
              <pre className="overflow-x-auto rounded-lg border border-line-soft bg-surface-2 p-4 text-base whitespace-pre-wrap">
                {result.message}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
