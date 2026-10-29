"use client";

import { useCallback, useState } from "react";
import { Notice } from "@/components/ui/Notice";

/** Executa uma ação assíncrona e guarda estado de carregamento, erro e sucesso. */
export function useAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  const run = useCallback(async <T,>(fn: () => Promise<T>, success?: string): Promise<T | undefined> => {
    setBusy(true);
    setError(null);
    setOk(null);
    try {
      const result = await fn();
      if (success) setOk(success);
      return result;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro inesperado. Tente de novo.");
      return undefined;
    } finally {
      setBusy(false);
    }
  }, []);

  const reset = useCallback(() => {
    setError(null);
    setOk(null);
  }, []);

  return { busy, error, ok, run, reset };
}

export function Feedback({ error, ok }: { error: string | null; ok: string | null }) {
  if (error) return <div className="reveal"><Notice tone="error">{error}</Notice></div>;
  if (ok) return <div className="reveal"><Notice tone="success">{ok}</Notice></div>;
  return null;
}
