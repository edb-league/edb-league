import { ImageResponse } from "next/og";
import { BODY_FONT, CREST_PNG, TITLE_FONT } from "./assets";

/** Tamanho padrão de pré-visualização de links (WhatsApp, Discord, X, Telegram). */
export const OG_SIZE = { width: 1200, height: 630 };
export const OG_TYPE = "image/png";

// Cores do tema escuro do site (tokens.css), fixas aqui porque a imagem não lê CSS.
const C = {
  bg: "#0a1524",
  surface: "#10233a",
  surface2: "#16304d",
  line: "#2a4668",
  text: "#f3f8fd",
  muted: "#bccedf",
  accent: "#7cc0f2",
  gold: "#e3c794",
  pt: "#ff9fb0",
  pl: "#9bcbff",
};

const DISPLAY = "Barlow Condensed";
const BODY = "Barlow";

export type OgStat = { label: string; value: string };
export type OgRow = { rank: number; name: string; value: string };
export type OgVersus = {
  left: string;
  right: string;
  scoreLeft: number | null;
  scoreRight: number | null;
  winner: "left" | "right" | null;
};
export type OgCard = {
  kicker: string;
  title: string;
  subtitle?: string;
  stars?: number;
  stats?: OgStat[];
  rows?: OgRow[];
  versus?: OgVersus;
};

function titleSize(text: string): number {
  if (text.length <= 12) return 150;
  if (text.length <= 20) return 112;
  if (text.length <= 28) return 84;
  return 64;
}

function Star() {
  return (
    <svg width="40" height="40" viewBox="0 0 24 24" fill={C.gold}>
      <path d="M12 2.5l2.9 6.1 6.6.8-4.9 4.6 1.3 6.6L12 17.3 6.1 20.6l1.3-6.6L2.5 9.4l6.6-.8z" />
    </svg>
  );
}

function sideColor(side: "left" | "right"): string {
  return side === "left" ? C.pt : C.pl;
}

function Versus({ v }: { v: OgVersus }) {
  const cell = (name: string, side: "left" | "right") => (
    <div style={{ display: "flex", flex: 1, justifyContent: side === "left" ? "flex-end" : "flex-start" }}>
      <div
        style={{
          display: "flex",
          fontFamily: DISPLAY,
          fontSize: 76,
          color: sideColor(side),
          opacity: v.winner && v.winner !== side ? 0.65 : 1,
        }}
      >
        {name}
      </div>
    </div>
  );
  const score = (n: number | null, side: "left" | "right") => (
    <div
      style={{
        display: "flex",
        fontFamily: DISPLAY,
        fontSize: 132,
        lineHeight: 1,
        color: v.winner === side ? C.gold : C.text,
        opacity: v.winner && v.winner !== side ? 0.7 : 1,
      }}
    >
      {n ?? "–"}
    </div>
  );
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 28, width: "100%" }}>
      {cell(v.left, "left")}
      {score(v.scoreLeft, "left")}
      <div style={{ display: "flex", fontFamily: DISPLAY, fontSize: 64, color: C.muted }}>×</div>
      {score(v.scoreRight, "right")}
      {cell(v.right, "right")}
    </div>
  );
}

function Rows({ rows }: { rows: OgRow[] }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10, width: "100%" }}>
      {rows.map((r) => (
        <div
          key={r.rank}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 24,
            padding: "8px 28px",
            borderRadius: 18,
            background: C.surface,
            border: `2px solid ${r.rank === 1 ? C.gold : C.line}`,
          }}
        >
          <div style={{ display: "flex", width: 56, fontFamily: DISPLAY, fontSize: 46, color: r.rank === 1 ? C.gold : C.accent }}>
            {r.rank}
          </div>
          <div
            style={{
              display: "flex",
              flex: 1,
              fontFamily: DISPLAY,
              fontSize: 46,
              color: C.text,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {r.name}
          </div>
          <div style={{ display: "flex", fontFamily: DISPLAY, fontSize: 46, color: r.rank === 1 ? C.gold : C.text }}>{r.value}</div>
        </div>
      ))}
    </div>
  );
}

function Stats({ stats }: { stats: OgStat[] }) {
  return (
    <div style={{ display: "flex", gap: 20, width: "100%" }}>
      {stats.map((s) => (
        <div
          key={s.label}
          style={{
            display: "flex",
            flexDirection: "column",
            flex: 1,
            padding: "18px 26px",
            borderRadius: 18,
            background: C.surface,
            border: `2px solid ${C.line}`,
          }}
        >
          <div style={{ display: "flex", fontFamily: DISPLAY, fontSize: 72, lineHeight: 1, color: C.text }}>{s.value}</div>
          <div style={{ display: "flex", fontFamily: BODY, fontSize: 26, color: C.muted, marginTop: 6 }}>{s.label}</div>
        </div>
      ))}
    </div>
  );
}

function Card({ card }: { card: OgCard }) {
  // Com ranking ou resultado, o título fica menor para dar espaço ao conteúdo.
  const compact = Boolean(card.rows || card.versus);
  const size = card.rows ? Math.min(titleSize(card.title), 76) : compact ? Math.min(titleSize(card.title), 96) : titleSize(card.title);
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        height: "100%",
        padding: "48px 72px 52px 84px",
        background: `linear-gradient(135deg, ${C.bg} 0%, ${C.surface} 100%)`,
        color: C.text,
        fontFamily: BODY,
        position: "relative",
      }}
    >
      <div style={{ display: "flex", position: "absolute", left: 0, top: 0, bottom: 0, width: 16, background: C.gold }} />
      <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
        {/* eslint-disable-next-line @next/next/no-img-element -- imagem de next/og, não do DOM */}
        <img src={CREST_PNG} height={64} width={64} alt="" style={{ objectFit: "contain" }} />
        <div style={{ display: "flex", fontFamily: DISPLAY, fontSize: 44, letterSpacing: 4, color: C.gold }}>EDB LEAGUE</div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", flex: 1, justifyContent: "center", gap: 6, paddingBottom: card.rows ? 14 : 0 }}>
        <div style={{ display: "flex", fontFamily: DISPLAY, fontSize: 40, letterSpacing: 3, color: C.accent, textTransform: "uppercase" }}>
          {card.kicker}
        </div>
        <div
          style={{
            display: "flex",
            fontFamily: DISPLAY,
            fontSize: size,
            lineHeight: 1.02,
            color: C.text,
            textTransform: "uppercase",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {card.title}
        </div>
        {(card.subtitle || card.stars) && (
          <div style={{ display: "flex", alignItems: "center", gap: 18, marginTop: 4 }}>
            {card.stars ? (
              <div style={{ display: "flex", gap: 4 }}>
                {Array.from({ length: card.stars }, (_, i) => (
                  <Star key={i} />
                ))}
              </div>
            ) : null}
            {card.subtitle && <div style={{ display: "flex", fontSize: 34, color: C.muted }}>{card.subtitle}</div>}
          </div>
        )}
      </div>

      {card.versus && <Versus v={card.versus} />}
      {card.rows && <Rows rows={card.rows} />}
      {card.stats && <Stats stats={card.stats} />}
    </div>
  );
}

/** Imagem 1200×630 no estilo do site (azul-marinho e dourado). */
export function ogImage(card: OgCard): ImageResponse {
  return new ImageResponse(<Card card={card} />, {
    ...OG_SIZE,
    fonts: [
      { name: DISPLAY, data: Buffer.from(TITLE_FONT, "base64"), weight: 700, style: "normal" },
      { name: BODY, data: Buffer.from(BODY_FONT, "base64"), weight: 600, style: "normal" },
    ],
  });
}
