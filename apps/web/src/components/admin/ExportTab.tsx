import { Card } from "@/components/ui/Card";

const FILES = [
  { name: "players", title: "Jogadores", text: "Elenco com nickname, SteamID e nível." },
  { name: "matches", title: "Partidas", text: "Uma linha por mapa, com data, placar e formato." },
  { name: "stats", title: "Estatísticas", text: "Uma linha por jogador em cada mapa." },
];

export function ExportTab() {
  return (
    <Card aria-labelledby="exportar-titulo">
      <h3 id="exportar-titulo" className="text-xl font-bold">Exportar dados</h3>
      <p className="mb-4 max-w-prose text-base text-muted">
        Arquivos CSV em UTF-8, prontos para abrir no Excel ou no Google Planilhas.
      </p>
      <ul className="grid gap-3 md:grid-cols-3">
        {FILES.map((f) => (
          <li key={f.name} className="rounded-lg border border-line-soft p-4">
            <p className="text-lg font-bold">{f.title}</p>
            <p className="mb-3 text-base text-muted">{f.text}</p>
            <a
              href={`/api/admin/export/${f.name}.csv`}
              download={`edb-${f.name}.csv`}
              className="inline-flex min-h-11 items-center rounded-lg border border-line bg-surface-2 px-4 py-2 text-base font-bold text-fg no-underline hover:bg-surface-3"
            >
              Baixar {f.title.toLowerCase()} (CSV)
            </a>
          </li>
        ))}
      </ul>
    </Card>
  );
}
