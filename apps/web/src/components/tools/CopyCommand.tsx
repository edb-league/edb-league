"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";

/** Linha de comando com botão de copiar. O texto vem pronto do servidor. */
export function CopyCommand({ command, label = "Copiar" }: { command: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Sem permissão de área de transferência: o texto continua selecionável na tela.
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <code className="min-w-0 flex-1 break-all rounded-lg border border-line bg-surface px-3 py-2 text-base">{command}</code>
      <Button variant="secondary" onClick={copy}>
        {copied ? "Copiado" : label}
      </Button>
    </div>
  );
}
