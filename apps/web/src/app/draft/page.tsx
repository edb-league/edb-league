import { DraftLive } from "@/components/draft/DraftLive";
import { PageHeader } from "@/components/ui/PageHeader";
import { api, steamAvatars } from "@/lib/api";
import type { DraftView, PlayerListItem } from "@/lib/types";

export const metadata = { title: "Draft" };
export const dynamic = "force-dynamic";

export default async function DraftPage() {
  const [draft, avatars, players] = await Promise.all([
    api<DraftView>("/draft", { revalidate: 0 }),
    steamAvatars(),
    api<PlayerListItem[]>("/players"),
  ]);
  return (
    <>
      <PageHeader
        title="Draft do campeonato"
        subtitle="Os capitães escolhem os jogadores em turnos, em ordem de cobra. Qualquer pessoa pode registrar as escolhas e todos acompanham ao vivo."
        art="duel"
      />
      <div className="mt-6">
        <DraftLive initial={draft} avatars={avatars} players={players.filter((p) => p.is_active)} />
      </div>
    </>
  );
}
