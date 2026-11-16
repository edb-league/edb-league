import { LobbyBoard } from "@/components/lobby/LobbyBoard";
import { CopyCommand } from "@/components/tools/CopyCommand";
import { Card, EmptyState } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { steamAvatars } from "@/lib/api";

export const metadata = { title: "Servidor" };

// Lido na hora do acesso: endereço e senha ficam nas variáveis de ambiente da Vercel,
// nunca no repositório (que é público).
export const dynamic = "force-dynamic";

const MATCH_COMMANDS = [
  [".ready", "Marca que você está pronto (todos precisam marcar para a partida começar)."],
  [".pause", "Pede pausa. Ela entra no início do próximo round."],
  [".unpause", "Pede para voltar. Os dois times precisam confirmar."],
  [".start", "Admin: força o início da partida sem esperar todos."],
  [".map nome_do_mapa", "Admin: troca o mapa. Exemplo: .map de_mirage"],
] as const;

export default async function ServerPage() {
  const avatars = await steamAvatars();
  const address = process.env.CS2_SERVER_ADDRESS?.trim();
  const password = process.env.CS2_SERVER_PASSWORD?.trim();
  const command = address ? `connect ${address}${password ? `; password ${password}` : ""}` : null;

  return (
    <>
      <PageHeader
        title="Servidor"
        subtitle="Como entrar no servidor de CS2 da liga e quais comandos usar durante a partida."
      />

      <section aria-labelledby="lobby-titulo" className="flex flex-col gap-3">
        <h2 id="lobby-titulo" className="text-3xl">Lobby da partida</h2>
        <p className="max-w-prose text-lg text-muted">
          Entre em um dos times. Quem chega primeiro em cada lado é o capitão e escolhe o mapa e o formato.
        </p>
        <LobbyBoard avatars={avatars} />
      </section>

      <Card aria-labelledby="entrar">
        <h2 id="entrar" className="text-3xl">Como entrar</h2>
        {command ? (
          <>
            <ol className="mt-3 max-w-prose list-decimal space-y-1.5 pl-6 text-lg text-muted">
              <li>No CS2, ative o console em Configurações, Jogo, &quot;Ativar console do desenvolvedor&quot;.</li>
              <li>Abra o console (tecla &apos; ou ~) e cole o comando abaixo.</li>
            </ol>
            <div className="mt-4">
              <CopyCommand command={command} label="Copiar comando" />
            </div>
            {!password && (
              <p className="mt-3 text-base text-muted">A senha do servidor está no Discord da liga. Acrescente-a ao comando: <code>; password SENHA</code>.</p>
            )}
          </>
        ) : (
          <EmptyState className="mt-3">O endereço do servidor ainda não foi divulgado. Fique de olho no Discord da liga.</EmptyState>
        )}
      </Card>

      <Card aria-labelledby="comandos">
        <h2 id="comandos" className="text-3xl">Comandos da partida</h2>
        <p className="mt-1 text-base text-muted">Digite no chat do jogo.</p>
        <dl className="mt-3 grid gap-x-6 gap-y-3 sm:grid-cols-[max-content_1fr]">
          {MATCH_COMMANDS.map(([cmd, text]) => (
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
