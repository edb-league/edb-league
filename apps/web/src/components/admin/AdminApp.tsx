"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";
import { Tabs } from "@/components/ui/Tabs";
import { ClientError, getJson, sendJson } from "@/lib/client";
import type { AdminOverview, AdminSession } from "@/lib/types";
import { ConfrontTab } from "./ConfrontTab";
import { ExportTab } from "./ExportTab";
import { ImportTab } from "./ImportTab";
import { LoginForm } from "./LoginForm";
import { RosterTab } from "./RosterTab";
import { SeasonsTab } from "./SeasonsTab";

type State =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "not-configured" }
  | { kind: "login" }
  | { kind: "ready"; overview: AdminOverview };

async function fetchState(): Promise<State> {
  try {
    const session = await getJson<AdminSession>("/admin/session");
    if (!session.configured) return { kind: "not-configured" };
    if (!session.authenticated) return { kind: "login" };
    const overview = await getJson<AdminOverview>("/admin/overview");
    return { kind: "ready", overview };
  } catch (e) {
    if (e instanceof ClientError && e.status === 401) return { kind: "login" };
    return { kind: "error", message: e instanceof Error ? e.message : "Falha ao carregar a administração." };
  }
}

export function AdminApp() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [loggingOut, setLoggingOut] = useState(false);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const next = await fetchState();
      if (!cancelled) setState(next);
    })();
    return () => {
      cancelled = true;
    };
  }, [version]);

  /** Recarrega a visão geral. Com `showLoading`, volta ao estado de carregamento antes. */
  const reload = useCallback((showLoading = false) => {
    if (showLoading) setState({ kind: "loading" });
    setVersion((v) => v + 1);
  }, []);

  async function logout() {
    setLoggingOut(true);
    try {
      await sendJson("POST", "/admin/logout");
    } finally {
      setLoggingOut(false);
      setState({ kind: "login" });
    }
  }

  if (state.kind === "loading") {
    return (
      <p role="status" className="text-base text-muted">
        Carregando administração...
      </p>
    );
  }
  if (state.kind === "error") {
    return (
      <div className="flex max-w-xl flex-col gap-4">
        <Notice tone="error" title="Não foi possível abrir a administração">
          {state.message}
        </Notice>
        <div>
          <Button onClick={() => reload(true)}>Tentar de novo</Button>
        </div>
      </div>
    );
  }
  if (state.kind === "not-configured") {
    return (
      <Notice tone="warning" title="Administração desativada" className="max-w-xl">
        Defina a variável de ambiente XINXAS_ADMIN_PASSWORD no servidor da API para liberar o acesso.
      </Notice>
    );
  }
  if (state.kind === "login") {
    return <LoginForm onLogin={() => reload(true)} />;
  }

  const { overview } = state;
  const refresh = () => reload();

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-base text-muted">
          {overview.players.filter((p) => p.is_active).length} jogadores ativos ·{" "}
          {overview.cloud ? "banco online" : "banco local (modo de teste)"}
        </p>
        <Button variant="secondary" onClick={logout} disabled={loggingOut}>
          {loggingOut ? "Saindo..." : "Sair da administração"}
        </Button>
      </div>
      <Tabs
        label="Seções da administração"
        tabs={[
          { value: "elenco", label: "Elenco", content: <RosterTab players={overview.players} onChanged={refresh} /> },
          { value: "importar", label: "Importar", content: <ImportTab onChanged={refresh} /> },
          { value: "confrontos", label: "Confrontos", content: <ConfrontTab overview={overview} onChanged={refresh} /> },
          { value: "temporadas", label: "Temporadas", content: <SeasonsTab overview={overview} onChanged={refresh} /> },
          { value: "exportar", label: "Exportar", content: <ExportTab /> },
        ]}
      />
    </div>
  );
}
