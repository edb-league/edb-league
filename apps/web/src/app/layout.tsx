import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import Link from "next/link";
import { api } from "@/lib/api";
import { NAV_ITEMS } from "@/lib/nav";
import type { Meta } from "@/lib/types";
// Fontes carregadas aqui (e não no CSS) para o Next resolver os pacotes, inclusive no Windows.
import "@fontsource/barlow/400.css";
import "@fontsource/barlow/500.css";
import "@fontsource/barlow/600.css";
import "@fontsource/barlow/700.css";
import "@fontsource/barlow-condensed/500.css";
import "@fontsource/barlow-condensed/600.css";
import "@fontsource/barlow-condensed/700.css";
import "./globals.css";

// Os dados mudam durante o dia; as consultas à API têm cache curto próprio.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: { default: "EDB LEAGUE", template: "%s · EDB LEAGUE" },
  description: "Rankings, partidas, jogadores e medalhas da liga EDB de Counter-Strike 2.",
  icons: { icon: "/crest.webp" },
  openGraph: { siteName: "EDB LEAGUE", locale: "pt_BR", type: "website" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  colorScheme: "light dark",
};

// Aplica o tema salvo antes da pintura para evitar o "flash" de tema errado.
const themeScript = `try{var t=localStorage.getItem('edb-theme');if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t)}catch(e){}`;

export default async function RootLayout({ children }: { children: ReactNode }) {
  let meta: Meta | null = null;
  try {
    meta = await api<Meta>("/meta");
  } catch {
    meta = null; // a própria página mostra o erro com mais contexto
  }

  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <a
          href="#conteudo"
          className="sr-only-focusable fixed top-2 left-2 z-50 rounded-lg bg-accent-bg px-4 py-3 text-base font-bold text-on-accent"
        >
          Pular para o conteúdo
        </a>
        <SiteHeader />
        <div>
          {meta?.demo && (
            <div className="border-b border-line-soft bg-surface-2 px-4 py-2 text-center text-base">
              <strong>Dados de demonstração.</strong> Os jogadores e partidas abaixo são fictícios.
            </div>
          )}
          <main id="conteudo" tabIndex={-1} className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-6 focus:outline-none md:px-8 md:py-8">
            {children}
          </main>
          <footer className="border-t border-line-soft bg-surface">
            <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-x-8 gap-y-3 px-4 py-6 text-base text-muted md:px-8">
              <p className="font-display text-xl font-bold tracking-wider text-fg uppercase">EDB League · CS2</p>
              <p className="max-w-prose">Os números vêm das partidas registradas e são atualizados a cada poucos minutos.</p>
              <nav aria-label="Rodapé">
                <ul className="flex flex-wrap gap-x-5">
                  {NAV_ITEMS.map((item) => (
                    <li key={item.href}>
                      <Link href={item.href} className="inline-flex min-h-11 items-center">
                        {item.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </nav>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
