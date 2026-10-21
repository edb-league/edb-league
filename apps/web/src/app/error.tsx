"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-start gap-4">
      <h1 className="text-3xl font-extrabold">Não foi possível carregar esta página</h1>
      <Notice tone="error">
        Os dados da liga não responderam agora. Isso costuma passar em alguns instantes. Tente de novo; se continuar,
        avise o administrador.
      </Notice>
      <Button onClick={() => reset()}>Tentar novamente</Button>
    </div>
  );
}
