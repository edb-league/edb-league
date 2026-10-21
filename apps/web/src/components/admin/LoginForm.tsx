"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { TextField } from "@/components/ui/Field";
import { sendJson } from "@/lib/client";
import { Feedback, useAction } from "./useAction";

export function LoginForm({ onLogin }: { onLogin: () => void }) {
  const [password, setPassword] = useState("");
  const action = useAction();

  return (
    <Card className="max-w-md" aria-labelledby="login-titulo">
      <h2 id="login-titulo" className="mb-1 text-2xl font-bold">
        Entrar como administrador
      </h2>
      <p className="mb-4 text-base text-muted">Somente o administrador da liga cadastra jogadores e importa partidas.</p>
      <form
        className="flex flex-col gap-4"
        onSubmit={async (event) => {
          event.preventDefault();
          const result = await action.run(() => sendJson<{ ok: boolean }>("POST", "/admin/login", { password }));
          if (result?.ok) {
            setPassword("");
            onLogin();
          }
        }}
      >
        <TextField
          id="admin-senha"
          label="Senha do administrador"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Feedback error={action.error} ok={null} />
        <Button type="submit" disabled={action.busy || password.length === 0}>
          {action.busy ? "Entrando..." : "Entrar"}
        </Button>
      </form>
    </Card>
  );
}
