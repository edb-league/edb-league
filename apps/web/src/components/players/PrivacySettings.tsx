"use client";

import { useEffect, useState } from "react";
import { SteamLogin } from "@/components/layout/UserMenu";
import { Button } from "@/components/ui/Button";
import { CheckboxField } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { getJson, sendJson } from "@/lib/client";
import type { Me, MyPrivacy } from "@/lib/types";

type Choices = Pick<MyPrivacy, "hide_avatar" | "hide_persona" | "hide_hours">;

const OPTIONS: { key: keyof Choices; label: string }[] = [
  { key: "hide_avatar", label: "Esconder minha foto da Steam" },
  { key: "hide_persona", label: "Esconder meu nome na Steam" },
  { key: "hide_hours", label: "Esconder minhas horas de CS" },
];

/** Escolhas da pessoa logada sobre o que da conta Steam dela aparece no site. */
export function PrivacySettings({ me }: { me: Me }) {
  const [saved, setSaved] = useState<MyPrivacy | null>(null);
  const [draft, setDraft] = useState<Choices | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "ok" | "error"; text: string } | null>(null);

  useEffect(() => {
    if (!me.player) return;
    let alive = true;
    getJson<MyPrivacy>("/me/privacy")
      .then((data) => {
        if (!alive) return;
        setSaved(data);
        setDraft({ hide_avatar: data.hide_avatar, hide_persona: data.hide_persona, hide_hours: data.hide_hours });
      })
      .catch(() => alive && setSaved(null));
    return () => {
      alive = false;
    };
  }, [me.player]);

  if (!me.authenticated || !me.player) {
    return (
      <div className="flex flex-wrap items-center gap-3">
        <p className="text-base">
          {me.login_enabled
            ? "Entre com a Steam, na conta de um jogador cadastrado, para escolher o que aparece."
            : "O login com a Steam não está ligado neste servidor."}
        </p>
        {me.login_enabled && <SteamLogin />}
      </div>
    );
  }
  if (!saved?.available || !draft) {
    return <p className="text-base">As escolhas de privacidade ainda não estão disponíveis neste servidor.</p>;
  }

  const changed = OPTIONS.some((o) => draft[o.key] !== saved[o.key]);

  async function save() {
    if (!draft) return;
    setBusy(true);
    setMessage(null);
    try {
      const next = await sendJson<MyPrivacy>("POST", "/me/privacy", draft);
      setSaved(next);
      setMessage({ tone: "ok", text: "Escolhas salvas. As fotos do site podem levar até 10 minutos para atualizar." });
    } catch (e) {
      setMessage({ tone: "error", text: e instanceof Error ? e.message : "Não foi possível salvar." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={(event) => {
        event.preventDefault();
        void save();
      }}
    >
      <fieldset className="flex flex-col gap-3">
        <legend className="mb-1 text-lg font-bold">O que aparece no seu perfil</legend>
        {OPTIONS.map((o) => (
          <CheckboxField
            key={o.key}
            id={`priv-${o.key}`}
            label={o.label}
            checked={draft[o.key]}
            onChange={(e) => setDraft({ ...draft, [o.key]: e.target.checked })}
          />
        ))}
      </fieldset>
      <div>
        <Button type="submit" disabled={busy || !changed}>
          {busy ? "Salvando..." : "Salvar escolhas"}
        </Button>
      </div>
      {message &&
        (message.tone === "ok" ? (
          <p role="status" className="text-base text-win">
            {message.text}
          </p>
        ) : (
          <Notice tone="error">{message.text}</Notice>
        ))}
    </form>
  );
}
