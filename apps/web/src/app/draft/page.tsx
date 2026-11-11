import { DraftLive } from "@/components/draft/DraftLive";
import { PageHeader } from "@/components/ui/PageHeader";
import { api, steamAvatars } from "@/lib/api";
import type { DraftView } from "@/lib/types";

export const metadata = { title: "Draft" };
export const dynamic = "force-dynamic";

export default async function DraftPage() {
  const [draft, avatars] = await Promise.all([api<DraftView>("/draft", { revalidate: 0 }), steamAvatars()]);
  return (
    <>
      <PageHeader
        title="Draft do campeonato"
        subtitle="Os capitães escolhem os jogadores em turnos, em ordem de cobra. O administrador registra cada escolha e a página mostra tudo ao vivo."
        art="duel"
      />
      <div className="mt-6">
        <DraftLive initial={draft} avatars={avatars} />
      </div>
    </>
  );
}
