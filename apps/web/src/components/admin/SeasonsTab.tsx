"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Notice } from "@/components/ui/Notice";
import { SelectField } from "@/components/ui/Field";
import { dateBR } from "@/lib/format";
import { sendJson } from "@/lib/client";
import type { AdminOverview } from "@/lib/types";
import { Feedback, useAction } from "./useAction";

export function SeasonsTab({ overview, onChanged }: { overview: AdminOverview; onChanged: () => void }) {
  const [target, setTarget] = useState(String(overview.pending_seasons[0]?.number ?? ""));
  const action = useAction();

  return (
    <Card aria-labelledby="homologacao">
      <h3 id="homologacao" className="text-xl font-bold">Homologação de temporadas encerradas</h3>
      <p className="mb-4 max-w-prose text-base text-muted">
        Confere os confrontos, congela os rankings Elite, Superação e XP e registra os títulos oficiais (MVP,
        Revelação e Xinxa). A operação não pode ser desfeita pelo site.
      </p>
      {!overview.cloud ? (
        <Notice tone="info">A homologação exige o banco online (Supabase).</Notice>
      ) : overview.pending_seasons.length === 0 ? (
        <p className="text-base text-muted">Não há temporadas encerradas pendentes de homologação.</p>
      ) : (
        <form
          className="flex max-w-md flex-col gap-4"
          onSubmit={async (event) => {
            event.preventDefault();
            const done = await action.run(
              () => sendJson<{ ok: boolean }>("POST", `/admin/seasons/${encodeURIComponent(target)}/homologate`),
              "Classificação, estrelas e títulos oficiais homologados.",
            );
            if (done) onChanged();
          }}
        >
          <SelectField id="temporada-homologar" label="Temporada para conferir" value={target} onChange={(e) => setTarget(e.target.value)}>
            {overview.pending_seasons.map((s) => (
              <option key={s.number} value={s.number}>
                {s.label} (até {dateBR(s.ends_on)})
              </option>
            ))}
          </SelectField>
          <Feedback error={action.error} ok={action.ok} />
          <Button type="submit" disabled={action.busy || !target}>
            {action.busy ? "Conferindo..." : "Conferir e homologar resultados"}
          </Button>
        </form>
      )}
    </Card>
  );
}
