import { LinkButton } from "@/components/ui/Button";

export const metadata = { title: "Página não encontrada" };

export default function NotFound() {
  return (
    <div className="flex flex-col items-start gap-4">
      <h1 className="text-3xl font-extrabold">Página não encontrada</h1>
      <p className="max-w-prose text-lg text-muted">
        O endereço pode ter mudado ou o jogador ou a partida não existe mais.
      </p>
      <LinkButton href="/" variant="primary">
        Voltar à visão geral
      </LinkButton>
    </div>
  );
}
