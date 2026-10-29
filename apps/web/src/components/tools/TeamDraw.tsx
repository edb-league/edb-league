"use client";

import clsx from "clsx";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Avatar } from "@/components/ui/Avatar";
import { TeamTag } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { controlClass } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { sendJson } from "@/lib/client";
import type { DrawResult } from "@/lib/types";
import { Icon } from "@/components/ui/Icon";

const TEAM_SIZE = 10;

export type RosterPlayer = { id: string; name: string; nickname: string; real_name: string | null; level: number; avatar?: string };

const BANDS = { "1-3": [1, 3], "4-6": [4, 6], "7-8": [7, 8], "9-10": [9, 10] } as const;

function TeamCard({ label, players, total, roster }: { label: "PT" | "PL"; players: DrawResult["team_a"]; total: number; roster: Map<string, RosterPlayer> }) {
  const sorted = [...players].sort((x, y) => y.level - x.level);
  return (
    <section
      aria-label={`Time ${label}`}
      className={clsx("rounded-xl border border-line-soft border-t-4 bg-surface-2 p-4", label === "PT" ? "border-t-pt" : "border-t-pl")}
    >
      <div className="mb-2 flex items-center justify-between border-b border-line-soft pb-3">
        <span className="text-xl">
          <TeamTag name={label} />
        </span>
        <span className="num text-4xl leading-none">
          {total} <span className="font-sans text-base font-medium text-muted">pontos</span>
        </span>
      </div>
      <ul>
        {sorted.map((p) => {
          const r = roster.get(p.id);
          const name = r?.nickname ?? p.name;
          return (
            <li key={p.id} className="flex min-h-14 items-center gap-3 text-lg">
              <Avatar name={name} src={r?.avatar} size={48} level={p.level} decorative className="border-2" />
              <span className="min-w-0 flex-1 font-bold break-words">{name}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

/** Dez vagas que se preenchem com a foto de cada jogador escolhido. */
function Slots({ selected, roster }: { selected: string[]; roster: Map<string, RosterPlayer> }) {
  return (
    <ul
      role="progressbar"
      aria-label="Jogadores selecionados"
      aria-valuemin={0}
      aria-valuemax={TEAM_SIZE}
      aria-valuenow={selected.length}
      aria-valuetext={`${selected.length} de ${TEAM_SIZE}`}
      className="mb-4 flex flex-wrap gap-2"
    >
      {Array.from({ length: TEAM_SIZE }, (_, i) => {
        const id = selected[i];
        const p = id ? roster.get(id) : undefined;
        return (
          <li key={i} aria-hidden="true" title={p?.nickname}>
            {p ? (
              <span className="reveal block">
                <Avatar name={p.nickname} src={p.avatar} size={40} decorative className="border-2" />
              </span>
            ) : (
              <span className="block size-10 rounded-full border-2 border-dashed border-line-soft" />
            )}
          </li>
        );
      })}
    </ul>
  );
}

function Step({ n, title, hint, state }: { n: number; title: string; hint: string; state: "done" | "current" | "todo" }) {
  return (
    <li
      aria-current={state === "current" ? "step" : undefined}
      className={clsx(
        "flex min-w-0 flex-[1_1_14rem] items-center gap-3 rounded-xl border bg-surface px-4 py-3",
        state === "current" ? "border-gold-bg" : "border-line-soft",
      )}
    >
      <span
        aria-hidden="true"
        className={clsx(
          "num inline-flex size-9 shrink-0 items-center justify-center rounded-full border-2 text-2xl leading-none",
          state === "todo" ? "border-line text-muted" : "border-gold-bg bg-gold-bg text-on-gold",
        )}
      >
        {state === "done" ? <Icon name="check" /> : n}
      </span>
      <span>
        <b className="block text-lg">
          {title}
          <span className="sr-only">{state === "done" ? " (concluída)" : state === "current" ? " (etapa atual)" : ""}</span>
        </b>
        <span className="text-base text-muted">{hint}</span>
      </span>
    </li>
  );
}

/** Sorteador 5 contra 5: escolhe 10 presentes e divide em dois times equilibrados pelo nível. */
export function TeamDraw({ roster }: { roster: RosterPlayer[] }) {
  const searchId = useId();
  const bandId = useId();
  const [selected, setSelected] = useState<string[]>([]);
  const [filter, setFilter] = useState("");
  const [band, setBand] = useState<"" | keyof typeof BANDS>("");
  const [result, setResult] = useState<DrawResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const resultRef = useRef<HTMLElement>(null);
  // Depois de sortear, leva o olhar ao resultado (que fica abaixo da lista), sem movimento se o usuário pediu menos.
  useEffect(() => {
    if (!result) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    resultRef.current?.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "nearest" });
  }, [result]);

  const byId = useMemo(() => new Map(roster.map((p) => [p.id, p])), [roster]);
  const visible = useMemo(() => {
    const term = filter.trim().toLocaleLowerCase("pt-BR");
    return roster.filter((p) => {
      if (term && !p.name.toLocaleLowerCase("pt-BR").includes(term)) return false;
      if (band && (p.level < BANDS[band][0] || p.level > BANDS[band][1])) return false;
      return true;
    });
  }, [roster, filter, band]);

  const full = selected.length >= TEAM_SIZE;
  const ready = selected.length === TEAM_SIZE;

  function toggle(id: string) {
    setResult(null);
    setError(null);
    setCopied(false);
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

  const stage = result ? 3 : ready ? 2 : 1;
  const state = (n: number): "done" | "current" | "todo" => (n < stage ? "done" : n === stage ? "current" : "todo");
  const total = result ? result.total_a + result.total_b : 0;

  return (
    <div className="flex flex-col gap-6">
      <ol aria-label="Etapas do sorteio" className="flex flex-wrap gap-3">
        <Step n={1} title="Escolher presentes" hint="10 jogadores, nem mais nem menos" state={state(1)} />
        <Step n={2} title="Sortear" hint="Divisão mais equilibrada pelo nível" state={state(2)} />
        <Step n={3} title="Compartilhar" hint="Copiar a mensagem para o grupo" state={state(3)} />
      </ol>

      <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-6">
        <Card aria-labelledby="presentes">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 id="presentes" className="text-3xl">1. Jogadores presentes</h2>
            <p aria-live="polite" className="text-lg font-bold text-gold">
              {selected.length} de {TEAM_SIZE} selecionados
            </p>
          </div>

          <div className="my-4 flex flex-wrap gap-3">
            <div className="flex min-w-48 flex-1 flex-col gap-1.5">
              <label htmlFor={searchId} className="text-base font-bold">Buscar jogador</label>
              <input id={searchId} type="search" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Digite parte do nome" className={controlClass} autoComplete="off" />
            </div>
            <div className="flex min-w-36 flex-col gap-1.5">
              <label htmlFor={bandId} className="text-base font-bold">Nível</label>
              <select id={bandId} className={controlClass} value={band} onChange={(e) => setBand(e.target.value as "" | keyof typeof BANDS)}>
                <option value="">Todos</option>
                {Object.keys(BANDS).map((b) => (
                  <option key={b} value={b}>Níveis {b.replace("-", " a ")}</option>
                ))}
              </select>
            </div>
          </div>

          <Slots selected={selected} roster={byId} />

          <fieldset>
            <legend className="sr-only">Jogadores presentes</legend>
            <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {visible.map((p) => {
                const checked = selected.includes(p.id);
                const id = `draw-${p.id}`;
                return (
                  <li key={p.id}>
                    <label
                      htmlFor={id}
                      className={clsx(
                        "flex min-h-14 cursor-pointer press items-center gap-3 rounded-xl border px-3 py-1.5 hover:bg-surface-2 has-[:disabled]:cursor-not-allowed has-[:disabled]:opacity-60",
                        checked ? "border-gold-bg bg-surface-2" : "border-line-soft bg-surface",
                      )}
                    >
                      <input id={id} type="checkbox" checked={checked} disabled={!checked && full} onChange={() => toggle(p.id)} />
                      <Avatar name={p.nickname} src={p.avatar} size={48} level={p.level} decorative className="border-2" />
                      <span className="min-w-0 flex-1">
                        <b className="block text-lg break-words">{p.nickname}</b>
                        <span className="block text-base text-muted">{p.real_name ?? "Nome real não cadastrado"}</span>
                      </span>
                    </label>
                  </li>
                );
              })}
              {visible.length === 0 && <li className="px-3 py-2 text-base text-muted">Nenhum jogador encontrado.</li>}
            </ul>
          </fieldset>

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Button variant="gold" onClick={draw} disabled={!ready || busy}>
              {busy ? "Sorteando..." : "Sortear times"}
            </Button>
            <Button variant="secondary" onClick={() => { setSelected([]); setResult(null); setError(null); setCopied(false); }} disabled={selected.length === 0}>
              Limpar seleção
            </Button>
          </div>
          {!ready && <p className="mt-3 text-base text-muted">Selecionar exatamente 10 jogadores libera o sorteio.</p>}
        </Card>

        <Card aria-labelledby="resultado" className={clsx("scroll-mt-4", result && "border-2 border-gold-bg")} ref={resultRef}>
          <h2 id="resultado" className="text-3xl">2. Resultado</h2>
          {error && <Notice tone="error" className="mt-4">{error}</Notice>}
          <div aria-live="polite">
            {result ? (
              <div className="mt-3 flex flex-col gap-5">
                <p className="text-lg text-muted">
                  Diferença de{" "}
                  <b className={result.gap === 0 ? "text-win" : "text-fg"}>
                    {result.gap === 0 && <span aria-hidden="true">▲ </span>}
                    {result.gap} {result.gap === 1 ? "ponto" : "pontos"}
                  </b>
                  . Sorteie de novo para outra combinação equilibrada.
                </p>
                <div>
                  <div
                    role="img"
                    aria-label={`Equilíbrio: PT ${result.total_a} pontos, PL ${result.total_b} pontos`}
                    className="flex h-4 overflow-hidden rounded-full"
                  >
                    <div className="bg-pt" style={{ flex: Math.max(result.total_a, 1) }} />
                    <div className="w-[3px] bg-bg" />
                    <div className="bg-pl" style={{ flex: Math.max(result.total_b, 1) }} />
                  </div>
                  <p aria-hidden="true" className="mt-1 flex justify-between text-base text-muted">
                    <span>PT {result.total_a}</span>
                    <span>{total} pontos no total</span>
                    <span>PL {result.total_b}</span>
                  </p>
                </div>
                <div key={result.message} className="reveal-list grid gap-4 md:grid-cols-2">
                  <TeamCard label="PT" players={result.team_a} total={result.total_a} roster={byId} />
                  <TeamCard label="PL" players={result.team_b} total={result.total_b} roster={byId} />
                </div>
                <div className="flex flex-wrap gap-3">
                  <Button variant="gold" onClick={draw} disabled={busy}>Sortear de novo</Button>
                  <Button variant="secondary" onClick={copy}>{copied ? "Copiado" : "Copiar mensagem"}</Button>
                </div>
                <div>
                  <h3 className="mb-2 font-display text-2xl font-bold uppercase">3. Mensagem para o grupo</h3>
                  <pre className="overflow-x-auto rounded-xl border border-line-soft bg-bg p-4 font-mono text-base leading-relaxed whitespace-pre-wrap">
                    {result.message}
                  </pre>
                </div>
              </div>
            ) : (
              <p className="mt-3 rounded-xl border border-dashed border-line p-6 text-center text-lg text-muted">
                {ready ? "Tudo pronto. Clique em Sortear times." : "Escolha 10 jogadores presentes para sortear os times."}
              </p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
