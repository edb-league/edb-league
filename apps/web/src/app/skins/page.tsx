import { Card, EmptyState } from "@/components/ui/Card";
import { LinkButton } from "@/components/ui/Button";
import { PageHeader } from "@/components/ui/PageHeader";
import { Icon } from "@/components/ui/Icon";

export const metadata = { title: "Skins" };

// Lido na hora do acesso: o endereço do site de skins fica nas variáveis de ambiente da Vercel.
export const dynamic = "force-dynamic";

const IN_GAME = [
  ["!skins", "Abre o menu de skins das armas."],
  ["!knife", "Escolhe o modelo da faca."],
  ["!gloves", "Escolhe as luvas."],
  ["!wp", "Atualiza as suas escolhas e aplica no jogo."],
] as const;

function safeUrl(raw: string | undefined): string | null {
  if (!raw) return null;
  try {
    const url = new URL(raw.trim());
    return url.protocol === "https:" || url.protocol === "http:" ? url.toString() : null;
  } catch {
    return null;
  }
}

export default function SkinsPage() {
  const siteUrl = safeUrl(process.env.CS2_SKINS_URL);

  return (
    <>
      <PageHeader
        title="Skins"
        subtitle="Escolha as skins das suas armas e da faca. Elas valem no servidor da liga."
      />

      <Card aria-labelledby="site">
        <h2 id="site" className="text-3xl">Escolher no site</h2>
        <p className="mt-1 max-w-prose text-lg text-muted">
          Entre com a sua conta Steam, escolha a skin, o desgaste e a faca. Depois use <code>!wp</code> no servidor para aplicar.
        </p>
        <div className="mt-4">
          {siteUrl ? (
            <LinkButton href={siteUrl} variant="gold" target="_blank" rel="noopener noreferrer">
              Abrir seletor de skins <Icon name="arrow-right" />
            </LinkButton>
          ) : (
            <EmptyState>O seletor de skins ainda não está disponível. Enquanto isso, use os comandos no jogo.</EmptyState>
          )}
        </div>
        <p className="mt-3 text-base text-muted">O site cobre facas e skins de armas. Luvas e agentes são escolhidos só no jogo.</p>
      </Card>

      <Card aria-labelledby="no-jogo">
        <h2 id="no-jogo" className="text-3xl">Escolher no jogo</h2>
        <p className="mt-1 text-base text-muted">Digite no chat do servidor.</p>
        <dl className="mt-3 grid gap-x-6 gap-y-3 sm:grid-cols-[max-content_1fr]">
          {IN_GAME.map(([cmd, text]) => (
            <div key={cmd} className="contents">
              <dt><code className="rounded-md bg-surface-3 px-2 py-1 text-base">{cmd}</code></dt>
              <dd className="text-lg text-muted">{text}</dd>
            </div>
          ))}
        </dl>
      </Card>
    </>
  );
}
