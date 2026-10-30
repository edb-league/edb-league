import Image from "next/image";
import Link from "next/link";
import { TierBadge } from "@/components/players/MedalCard";
import { MedalShape } from "@/components/players/MedalCard";
import { Card } from "@/components/ui/Card";
import { LEVEL_TIERS } from "@/components/ui/LevelBadge";
import { TocNav } from "@/components/layout/TocNav";
import { PageHeader } from "@/components/ui/PageHeader";
import { Stat } from "@/components/ui/Stat";
import { api } from "@/lib/api";
import { num, plural } from "@/lib/format";
import type { MedalCatalogue, Meta, Missions, Ranking, RankingType } from "@/lib/types";
import { Icon, StarRow } from "@/components/ui/Icon";

export const metadata = { title: "Regulamento" };

const SECTIONS = [
  ["temporadas", "1. Temporadas"],
  ["confrontos", "2. Confrontos"],
  ["pontuacao", "3. Pontuação e rankings"],
  ["titulos", "4. Títulos"],
  ["xp", "5. XP, níveis e medalhas"],
  ["perguntas", "6. Perguntas frequentes"],
] as const;

const RANKINGS: { type: RankingType; name: string; min: string }[] = [
  { type: "elite", name: "Elite", min: "6 mapas para concorrer ao título. Antes disso a posição é provisória." },
  { type: "superacao", name: "Superação", min: "6 mapas para premiação." },
  { type: "xp", name: "XP", min: "6 mapas para concorrer ao título." },
  { type: "bagres", name: "BAGRES", min: "Menos de 2 mapas: provisório." },
];

const LEVEL_BANDS = [
  { label: "1 a 3", level: 3 },
  { label: "4 a 6", level: 6 },
  { label: "7 a 8", level: 8 },
  { label: "9 e 10", level: 10 },
] as const;

const STATUS = [
  ["A iniciar", "A data de início ainda não chegou."],
  ["Em andamento", "Mostra o dia atual e quantos dias restam."],
  ["Encerrada", "Aguardando a homologação dos resultados."],
  ["Homologada", "Resultados fechados e títulos entregues."],
] as const;

const FAQ = [
  ["Quantos mapas preciso jogar para concorrer aos títulos?", "Pelo menos 6 mapas na temporada. Antes disso o jogador aparece como provisório nos rankings."],
  ["Existe limite de confrontos?", "Não. BO1 e BO3 são livres, sem limite de confrontos ou mapas por temporada. Contam os 6 melhores mapas de cada jogador em cada ranking."],
  ["Quando os títulos são entregues?", "Depois que a temporada encerra e os resultados são homologados. Até lá, a classificação é provisória."],
  ["O Sorteador muda alguma classificação?", "Não. Ele só divide os presentes em dois times e não registra partidas."],
] as const;

const H2 = "flex items-center gap-3 text-3xl md:text-4xl";
const NO = "num inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-gold-bg text-2xl leading-none text-on-gold";

export default async function RulesPage() {
  const [[meta, missions, cat], rankings] = await Promise.all([
    Promise.all([api<Meta>("/meta"), api<Missions>("/missions"), api<MedalCatalogue>("/medals")]),
    Promise.all(RANKINGS.map((r) => api<Ranking>(`/rankings/${r.type}`))),
  ]);
  const current = meta.seasons.find((s) => s.number === meta.current_season);
  const statusIndex = current ? { upcoming: 0, active: 1, closed_pending: 2, homologated: 3, unknown: -1 }[current.status] : -1;

  return (
    <>
      <PageHeader
        title="Regulamento"
        subtitle="Como funcionam as temporadas, os rankings, os títulos e a experiência. Tudo em um só lugar."
      />

      <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-8 xl:grid-cols-[15rem_minmax(0,1fr)]">
        <TocNav sections={SECTIONS} />

        <div className="flex min-w-0 flex-col gap-4">
          <Card aria-labelledby="sobre" className="flex flex-wrap items-center gap-6">
            <div className="relative aspect-[4/5] w-20 shrink-0 overflow-hidden rounded-lg border border-line-soft bg-surface-2">
              <Image src="/president.avif" alt="Retrato cerimonial do Presidente Dudu no Elenco de Bosta" fill sizes="5rem" className="object-contain" />
            </div>
            <div className="min-w-0 flex-1 basis-64">
              <h2 id="sobre" className="text-3xl">Inaugurada na gestão do Presidente Dudu</h2>
              <p className="num mt-1 text-2xl text-gold">15 de outubro de 2026</p>
            </div>
          </Card>

          <Card id="temporadas" aria-labelledby="t1" className="scroll-mt-24">
            <h2 id="t1" className={H2}><span aria-hidden="true" className={NO}>1</span>Temporadas</h2>
            <p className="mt-3 max-w-prose text-lg text-muted">
              A cada temporada, uma nova disputa começa e os rankings são reiniciados. Jogue quantas vezes quiser, acompanhe sua
              evolução e tente conquistar as primeiras posições. Cada novo mapa pode melhorar sua classificação.
            </p>
            <dl className="mt-3 grid gap-2 sm:grid-cols-3 md:gap-3">
              <Stat label="Duração" value="1 mês" hint="Do dia 19 ao dia 18 do mês seguinte. A Temporada 1 começou em 15/10, dia da primeira partida." />
              <Stat label="Rankings" value="Reiniciam" hint="Toda nova temporada começa do zero" />
              <Stat label="Mapas que contam" value="Top 6" hint="Os 6 melhores de cada jogador, em cada ranking" />
            </dl>
            <h3 className="mt-6 mb-2 font-display text-2xl font-bold uppercase">Situação de uma temporada</h3>
            <ol aria-label="Etapas de uma temporada" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {STATUS.map(([name, text], i) => (
                <li
                  key={name}
                  aria-current={i === statusIndex ? "step" : undefined}
                  className={`rounded-xl border bg-surface-2 p-4 ${i === statusIndex ? "border-gold-bg" : "border-line-soft"}`}
                >
                  <b className="block text-lg">
                    {name}
                    {i === statusIndex && current && <span className="ml-2 text-base font-normal text-gold">· {current.label}, agora</span>}
                  </b>
                  <span className="text-base text-muted">{text}</span>
                </li>
              ))}
            </ol>
          </Card>

          <Card id="confrontos" aria-labelledby="t2" className="scroll-mt-24">
            <h2 id="t2" className={H2}><span aria-hidden="true" className={NO}>2</span>Confrontos</h2>
            <p className="mt-3 max-w-prose text-lg text-muted">
              Os confrontos são BO1 e BO3 livres: não há limite de confrontos nem de mapas por temporada. Cada mapa conta
              igualmente na pontuação, seja de um BO1 avulso ou de uma série de três mapas.
            </p>
            <dl className="mt-3 grid gap-2 sm:grid-cols-3 md:gap-3">
              <Stat label="BO1" value="1 mapa" hint="Partida avulsa" />
              <Stat label="BO3" value="Até 3 mapas" hint="Série com placar de mapas" />
              <Stat label="Limite" value="Nenhum" hint="Confrontos e mapas por temporada" />
            </dl>
            <p className="mt-4">
              <Link href="/partidas" className="link-cta">Ver o histórico de partidas <Icon name="arrow-right" /></Link>
            </p>
          </Card>

          <Card id="pontuacao" aria-labelledby="t3" className="scroll-mt-24">
            <h2 id="t3" className={H2}><span aria-hidden="true" className={NO}>3</span>Pontuação e rankings</h2>
            <p className="mt-3 max-w-prose text-lg text-muted">
              São quatro rankings. Elite, Superação e XP valem títulos; o BAGRES é a brincadeira da casa. Até o jogador somar o
              mínimo de mapas, a posição é provisória.
            </p>
            <div role="region" aria-label="Os quatro rankings da liga" tabIndex={0} className="relative mt-4 overflow-x-auto rounded-lg border border-line-soft">
              <table className="w-full text-base">
                <caption className="sr-only">Os quatro rankings da liga, como são calculados e o mínimo para valer</caption>
                <thead>
                  <tr>
                    <th scope="col" className="bg-surface-2 px-3 py-2.5 text-left text-sm font-bold text-muted">Ranking</th>
                    <th scope="col" className="bg-surface-2 px-3 py-2.5 text-left text-sm font-bold text-muted">Como é calculado</th>
                    <th scope="col" className="bg-surface-2 px-3 py-2.5 text-left text-sm font-bold text-muted">Mínimo para valer</th>
                  </tr>
                </thead>
                <tbody>
                  {RANKINGS.map((r, i) => (
                    <tr key={r.type}>
                      <th scope="row" className="min-w-32 border-t border-line-soft px-3 py-3 text-left align-top text-lg">
                        <Link href={`/rankings/${r.type}`}>{r.name}</Link>
                      </th>
                      <td className="border-t border-line-soft px-3 py-3 align-top text-muted">
                        {(rankings[i]?.notes ?? []).slice(0, 2).map((n) => (
                          <p key={n} className="mb-1.5 last:mb-0">{n}</p>
                        ))}
                      </td>
                      <td className="min-w-48 border-t border-line-soft px-3 py-3 align-top">{r.min}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card id="titulos" aria-labelledby="t4" className="scroll-mt-24">
            <h2 id="t4" className={H2}><span aria-hidden="true" className={NO}>4</span>Títulos</h2>
            <p className="mt-3 max-w-prose text-lg text-muted">
              Para concorrer aos títulos é necessário disputar pelo menos 6 mapas. Os únicos títulos competitivos oficiais são
              os três abaixo, homologados após o encerramento da temporada.
            </p>
            <dl className="mt-3 grid gap-2 sm:grid-cols-3 md:gap-3">
              <Stat className="border-2 border-gold-bg" label="MVP" value="Elite" hint="Líder do ranking Elite" />
              <Stat label="Revelação" value="Superação" hint="Líder do ranking Superação" />
              <Stat label="Xinxa" value="XP" hint="Líder do ranking XP" />
            </dl>
            <p className="mt-4 max-w-prose text-lg text-muted">
              O Prêmio Henio, para o jogador com pior ADR, é uma homenagem da liga e aparece no <Link href="/hall-da-fama">Hall da Fama</Link>.
            </p>
          </Card>

          <Card id="xp" aria-labelledby="t5" className="scroll-mt-24">
            <h2 id="t5" className={H2}><span aria-hidden="true" className={NO}>5</span>XP, níveis e medalhas</h2>
            <p className="mt-3 max-w-prose text-lg text-muted">
              Todo nível tem uma meta. O prêmio é igual; o desafio é proporcional. Concluir uma partida de pelo menos 8 rounds
              com KPR igual ou acima da meta rende 100 XP, uma vez a cada semana da temporada.
            </p>
            <div className="mt-4 grid gap-6 md:grid-cols-2">
              <div>
                <h3 className="mb-2 font-display text-2xl font-bold uppercase">Meta semanal de kills por round</h3>
                <div role="region" aria-label="Meta de KPR por número de estrelas" tabIndex={0} className="overflow-x-auto rounded-lg border border-line-soft">
                  <table className="w-full text-base">
                    <caption className="sr-only">Meta de kills por round, por número de estrelas</caption>
                    <thead>
                      <tr>
                        <th scope="col" className="bg-surface-2 px-3 py-2.5 text-left text-sm font-bold text-muted">Estrelas</th>
                        <th scope="col" className="bg-surface-2 px-3 py-2.5 text-right text-sm font-bold text-muted">Meta de KPR</th>
                      </tr>
                    </thead>
                    <tbody>
                      {missions.targets.map((t) => (
                        <tr key={t.stars}>
                          <th scope="row" className="border-t border-line-soft px-3 py-2.5 text-left font-semibold">
                            <StarRow count={t.stars} className="mr-2 text-gold" />
                            {plural(t.stars, "estrela", "estrelas")}
                          </th>
                          <td className="num border-t border-line-soft px-3 py-2.5 text-right text-2xl">{num(t.kpr, 2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div>
                <h3 className="mb-2 font-display text-2xl font-bold uppercase">Como o XP é ganho</h3>
                <dl className="flex flex-col gap-2">
                  {[
                    ["Presença, por mapa", "+40"],
                    ["Vitória, por mapa", "+20"],
                    ["Missão semanal", "+100"],
                  ].map(([label, value]) => (
                    <div key={label} className="card flex items-baseline justify-between gap-3 px-4 py-3">
                      <dt className="text-lg">{label}</dt>
                      <dd className="num text-3xl leading-none">{value}</dd>
                    </div>
                  ))}
                </dl>
                <p className="mt-3 text-base text-muted">Contam 6 mapas na temporada, escolhidos para render o máximo de XP: o site considera a missão de cada semana ao escolher. Os 100 XP da missão só vêm de um desses 6 mapas.</p>
              </div>
            </div>
            <div className="mt-6 grid gap-6 md:grid-cols-2">
              <div id="niveis" className="scroll-mt-24">
                <h3 className="mb-2 font-display text-2xl font-bold uppercase">Níveis e estrelas</h3>
                <p className="text-base text-muted">
                  Cada jogador tem um nível de 1 a 10 no cadastro. O nível equilibra os times no Sorteador; as estrelas, de 1 a 5,
                  definem a meta semanal de KPR. A cor do selo só agrupa as faixas, o número sempre aparece escrito.
                </p>
                <ul className="mt-3 grid grid-cols-2 gap-2">
                  {LEVEL_BANDS.map((b) => (
                    <li key={b.label} className="flex items-center gap-2 rounded-xl border border-line-soft bg-surface-2 p-2">
                      <span className={`num inline-flex h-9 min-w-14 items-center justify-center rounded-lg px-2 text-2xl leading-none ${b.level <= 3 ? LEVEL_TIERS[0] : b.level <= 6 ? LEVEL_TIERS[1] : b.level <= 8 ? LEVEL_TIERS[2] : LEVEL_TIERS[3]}`}>
                        {b.label.replace(" a ", "–").replace(" e ", "–")}
                      </span>
                      <span className="text-base">Níveis {b.label}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div id="medalhas" className="scroll-mt-24">
                <h3 className="mb-2 font-display text-2xl font-bold uppercase">Medalhas</h3>
                <p className="text-base text-muted">
                  Marcos individuais em três faixas, com barra de progresso no perfil de cada jogador.
                </p>
                <ul className="mt-3 grid grid-cols-3 gap-2">
                  {(["bronze", "silver", "gold"] as const).map((tier) => (
                    <li key={tier} className="flex flex-col items-center gap-1 rounded-xl border border-line-soft bg-surface-2 p-2 text-center">
                      <MedalShape tier={tier} earned />
                      <TierBadge tier={tier} />
                      <span className="text-sm text-muted">{plural(cat.medals.filter((m) => m.tier === tier).length, "medalha", "medalhas")}</span>
                    </li>
                  ))}
                </ul>
                <p className="mt-2">
                  <Link href="/medalhas" className="link-cta">Ver todas as medalhas <Icon name="arrow-right" /></Link>
                </p>
              </div>
            </div>
            <p className="mt-2">
              <Link href="/missoes-xp" className="link-cta">Ver as missões da temporada <Icon name="arrow-right" /></Link>
            </p>
          </Card>

          <Card id="perguntas" aria-labelledby="t8" className="scroll-mt-24">
            <h2 id="t8" className={H2}><span aria-hidden="true" className={NO}>6</span>Perguntas frequentes</h2>
            <div className="mt-4 flex flex-col gap-2.5">
              {FAQ.map(([q, a]) => (
                <details key={q} className="rounded-xl border border-line-soft bg-surface-2 px-4">
                  <summary className="flex min-h-13 cursor-pointer items-center text-lg font-semibold">{q}</summary>
                  <p className="pb-4 text-lg text-muted">{a}</p>
                </details>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
