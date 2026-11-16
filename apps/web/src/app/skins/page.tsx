import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { SkinInventory } from "@/components/skins/SkinInventory";
import { getSkinCatalog } from "@/lib/skins";

export const metadata = { title: "Skins" };

const IN_GAME = [
  ["!skins", "Abre o menu de skins das armas."],
  ["!knife", "Escolhe o modelo da faca."],
  ["!gloves", "Escolhe as luvas."],
  ["!wp", "Atualiza as suas escolhas e aplica no jogo."],
] as const;

export default async function SkinsPage() {
  const catalog = await getSkinCatalog();
  return (
    <>
      <PageHeader
        title="Skins"
        subtitle="Escolha as skins das suas armas e da faca. Elas valem no servidor da liga."
      />

      <SkinInventory catalog={catalog} />

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
