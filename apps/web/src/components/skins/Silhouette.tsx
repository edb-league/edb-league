import type { Category } from "./inventory-data";

/*
 * Arte de reserva para quem ainda não escolheu skin: um desenho simples por tipo de arma, feito aqui
 * (não reproduz o modelo de nenhuma arma, faca ou luva real). Duas camadas de cor mais um traço de destaque.
 */
const BODY = "fill-line";
const DARK = "fill-muted opacity-60";
const ACCENT = "fill-accent";

function Art({ category }: { category: Category }) {
  switch (category) {
    case "knife":
      return (
        <g>
          <path className={BODY} d="M60 24 L116 21 Q142 23 153 35 Q126 37 60 37 Z" />
          <path className={ACCENT} d="M60 24 L116 21 Q132 22 142 28 L116 24 Z" opacity="0.85" />
          <rect className={DARK} x="54" y="18" width="7" height="22" rx="2" />
          <rect className={BODY} x="14" y="23" width="41" height="14" rx="6" />
          {[24, 31, 38, 45].map((x) => <rect key={x} className={DARK} x={x} y="23" width="2.5" height="14" />)}
          <circle className={DARK} cx="14" cy="30" r="5" />
        </g>
      );
    case "gloves":
      return (
        <g transform="translate(-18 -14) scale(1.35)">
          {([[60, 12], [70, 7], [80, 11], [90, 17]] as const).map(([x, top]) => (
            <rect key={x} className={BODY} x={x} y={top} width="9" height={34 - top} rx="4.5" />
          ))}
          <rect className={BODY} x="60" y="26" width="39" height="22" rx="4" />
          <rect className={BODY} x="47" y="26" width="9" height="22" rx="4.5" transform="rotate(-32 51 38)" />
          <rect className={DARK} x="58" y="45" width="43" height="13" rx="3" />
          <rect className={ACCENT} x="58" y="48" width="43" height="2.5" opacity="0.85" />
        </g>
      );
    case "sniper":
      return (
        <g>
          <path className={BODY} d="M4 28 L40 26 V42 L12 46 Q4 46 4 38 Z" />
          <rect className={BODY} x="40" y="24" width="36" height="12" rx="2" />
          <rect className={BODY} x="76" y="28" width="78" height="3" />
          <rect className={DARK} x="148" y="26" width="9" height="7" rx="1.5" />
          <rect className={DARK} x="54" y="20" width="3" height="5" />
          <rect className={DARK} x="86" y="20" width="3" height="5" />
          <rect className={DARK} x="50" y="11" width="46" height="9" rx="4" />
          <ellipse className={ACCENT} cx="49" cy="15.5" rx="2.6" ry="6" />
          <ellipse className={BODY} cx="97" cy="15.5" rx="3" ry="5" />
          <rect className={DARK} x="68" y="21" width="9" height="3" />
          <circle className={DARK} cx="79" cy="22.5" r="2.5" />
          <rect className={BODY} x="53" y="36" width="12" height="13" rx="2" />
          <path className={BODY} d="M44 36 L39 54 H48 L53 36 Z" />
        </g>
      );
    case "pistol":
      return (
        <g transform="translate(-4 0)">
          <rect className={BODY} x="46" y="16" width="70" height="14" rx="3" />
          {[84, 89, 94, 99].map((x) => <rect key={x} className={DARK} x={x} y="18" width="2" height="10" />)}
          <rect className={DARK} x="114" y="19" width="9" height="8" rx="2" />
          <rect className={ACCENT} x="52" y="19" width="26" height="2.5" opacity="0.85" />
          <rect className={DARK} x="48" y="12.5" width="5" height="3.5" />
          <rect className={DARK} x="108" y="12.5" width="4" height="3.5" />
          <rect className={BODY} x="50" y="30" width="58" height="7" />
          <path className={BODY} d="M56 30 H72 L66 56 Q65.5 59 62.5 59 H55 Q51.5 59 52 55.5 Z" />
          <path d="M78 37 V42 Q78 46 82 46 H90 Q94 46 94 42 V37" fill="none" strokeWidth="3" className="stroke-line" />
        </g>
      );
    case "smg":
      return (
        <g>
          <path className={BODY} d="M32 24 H12 Q8 24 8 28 V42 H13 V29 H32 Z" />
          <rect className={BODY} x="32" y="21" width="68" height="15" rx="3" />
          <rect className={DARK} x="98" y="23" width="22" height="11" rx="2" />
          <rect className={BODY} x="120" y="26.5" width="28" height="4" />
          <rect className={DARK} x="146" y="25" width="7" height="7" rx="1.5" />
          <rect className={ACCENT} x="36" y="25" width="30" height="2.5" opacity="0.85" />
          <rect className={DARK} x="48" y="17" width="14" height="4" />
          <path className={BODY} d="M72 36 H84 L82 60 H70 Z" />
          <path className={BODY} d="M40 36 L34 55 H43 L48 36 Z" />
        </g>
      );
    case "shotgun":
      return (
        <g>
          <path className={BODY} d="M4 28 L46 26 V40 L12 46 Q4 46 4 38 Z" />
          <rect className={BODY} x="46" y="24" width="26" height="14" rx="2" />
          <rect className={BODY} x="72" y="25.5" width="82" height="4.5" />
          <rect className={BODY} x="72" y="32" width="76" height="4" />
          <rect className={DARK} x="150" y="21" width="4" height="5" />
          <rect className={DARK} x="92" y="29" width="26" height="11" rx="4" />
          <rect className={ACCENT} x="96" y="33" width="18" height="2.5" opacity="0.85" />
          <path d="M56 38 V42 Q56 46 60 46 H66 Q70 46 70 42 V38" fill="none" strokeWidth="3" className="stroke-line" />
        </g>
      );
    case "mg":
      return (
        <g>
          <path className={BODY} d="M6 26 L36 24 V42 L12 46 Q6 46 6 38 Z" />
          <rect className={BODY} x="36" y="20" width="46" height="16" rx="3" />
          <path className={DARK} d="M44 20 Q56 10 70 20 Z" />
          <rect className={DARK} x="82" y="22" width="32" height="10" rx="2" />
          <rect className={BODY} x="114" y="25" width="26" height="4" />
          <rect className={DARK} x="138" y="23" width="8" height="8" rx="1.5" />
          <rect className={ACCENT} x="40" y="25" width="38" height="2.5" opacity="0.85" />
          <rect className={BODY} x="50" y="36" width="26" height="19" rx="3" />
          {[58, 64, 70].map((x) => <circle key={x} className={DARK} cx={x} cy="45" r="2" />)}
          <path d="M112 31 L104 56 M112 31 L120 56" fill="none" strokeWidth="2.5" className="stroke-line" />
          <path className={BODY} d="M40 36 L35 54 H44 L49 36 Z" />
        </g>
      );
    default:
      return (
        <g>
          <path className={BODY} d="M4 24 L40 22 V38 L10 42 Q4 42 4 36 Z" />
          <rect className={BODY} x="40" y="20" width="36" height="15" rx="2" />
          <rect className={DARK} x="76" y="22" width="34" height="11" />
          <rect className={BODY} x="110" y="25.5" width="38" height="3.5" />
          <rect className={DARK} x="146" y="24" width="7" height="6.5" rx="1.5" />
          <rect className={ACCENT} x="44" y="24" width="30" height="2.5" opacity="0.85" />
          <rect className={DARK} x="56" y="16" width="10" height="4" />
          <path className={DARK} d="M116 21 L118 16 H122 L123 21 Z" />
          <path className={BODY} d="M60 35 H74 L70 58 Q69 60 66 60 H60 Q57 60 57.5 57 Z" />
          <path className={BODY} d="M44 35 L38 54 H47 L52 35 Z" />
        </g>
      );
  }
}

/** Desenho de reserva (decorativo) com um brilho suave atrás, para casas sem skin escolhida. */
export function Silhouette({ category }: { category: Category }) {
  return (
    <span
      aria-hidden="true"
      className="flex h-24 w-full items-center justify-center"
      style={{ background: "radial-gradient(closest-side, color-mix(in srgb, var(--accent) 16%, transparent), transparent)" }}
    >
      <svg viewBox="0 0 160 64" className="h-16 w-40 max-w-full overflow-visible">
        <Art category={category} />
      </svg>
    </span>
  );
}
