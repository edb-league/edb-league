import clsx from "clsx";

/**
 * Padrões geométricos por mapa, em azul e ouro. Não são imagens dos mapas: dão a cada um uma
 * identidade reconhecível de relance. O nome do mapa sempre vem em texto ao lado.
 */
type Motif = "dunes" | "arches" | "grid" | "rings" | "bars" | "chevrons" | "stairs" | "diamonds";

const MOTIFS: Record<string, { motif: Motif; angle: number; spot: [number, number] }> = {
  dust2: { motif: "dunes", angle: 120, spot: [74, 30] },
  mirage: { motif: "arches", angle: 140, spot: [28, 36] },
  inferno: { motif: "stairs", angle: 100, spot: [70, 62] },
  nuke: { motif: "rings", angle: 160, spot: [50, 50] },
  overpass: { motif: "bars", angle: 110, spot: [30, 66] },
  ancient: { motif: "diamonds", angle: 130, spot: [66, 38] },
  anubis: { motif: "chevrons", angle: 150, spot: [38, 54] },
  vertigo: { motif: "grid", angle: 90, spot: [72, 28] },
  train: { motif: "bars", angle: 125, spot: [26, 40] },
};
const FALLBACK = { motif: "grid" as Motif, angle: 135, spot: [60, 40] as [number, number] };

function key(map: string): string {
  return map.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]/g, "");
}

function Pattern({ motif }: { motif: Motif }) {
  const common = { fill: "none", stroke: "var(--map-line)", strokeWidth: 1.5 } as const;
  switch (motif) {
    case "dunes":
      return (
        <g {...common}>
          {[40, 58, 76, 94].map((y) => (
            <path key={y} d={`M-10 ${y} Q 25 ${y - 22} 60 ${y} T 130 ${y}`} />
          ))}
        </g>
      );
    case "arches":
      return (
        <g {...common}>
          {[0, 1, 2, 3].map((i) => (
            <path key={i} d={`M${i * 34 - 6} 100 V60 a17 17 0 0 1 34 0 V100`} />
          ))}
        </g>
      );
    case "stairs":
      return <path {...common} d="M0 100 H22 V82 H44 V64 H66 V46 H88 V28 H110 V10 H130" />;
    case "rings":
      return (
        <g {...common}>
          {[16, 30, 44, 58].map((r) => (
            <circle key={r} cx="60" cy="50" r={r} />
          ))}
        </g>
      );
    case "bars":
      return (
        <g {...common}>
          {[8, 30, 52, 74, 96, 118].map((x) => (
            <path key={x} d={`M${x} 0 V100`} />
          ))}
          <path d="M0 62 H130" />
        </g>
      );
    case "diamonds":
      return (
        <g {...common}>
          {[0, 1, 2].map((i) => (
            <path key={i} d={`M${20 + i * 38} 50 l18 -28 l18 28 l-18 28 z`} />
          ))}
        </g>
      );
    case "chevrons":
      return (
        <g {...common}>
          {[0, 1, 2, 3].map((i) => (
            <path key={i} d={`M${-10 + i * 28} 10 L${18 + i * 28} 50 L${-10 + i * 28} 90`} />
          ))}
        </g>
      );
    default:
      return (
        <g {...common}>
          {[20, 40, 60, 80].map((v) => (
            <path key={v} d={`M0 ${v} H130 M${v * 1.3} 0 V100`} />
          ))}
        </g>
      );
  }
}

/** Faixa decorativa com o padrão do mapa; o conteúdo (nome, data) vai por cima, em texto. */
export function MapTile({
  map,
  className,
  compact,
  children,
}: {
  map: string;
  className?: string;
  /** Sem o padrão geométrico, só degradê e ponto dourado: para faixas pequenas. */
  compact?: boolean;
  children?: React.ReactNode;
}) {
  const style = MOTIFS[key(map)] ?? FALLBACK;
  return (
    <div
      className={clsx("relative isolate overflow-hidden", className)}
      style={{ backgroundImage: `linear-gradient(${style.angle}deg, var(--map-from), var(--map-to))` }}
    >
      {compact ? (
        <span aria-hidden="true" className="absolute top-1/2 left-2 -z-10 size-2 -translate-y-1/2 rounded-full bg-gold-bg" />
      ) : (
      <svg
        aria-hidden="true"
        viewBox="0 0 120 100"
        preserveAspectRatio="xMidYMid slice"
        className="absolute inset-0 -z-10 size-full opacity-80"
      >
        <Pattern motif={style.motif} />
        <circle cx={style.spot[0]} cy={style.spot[1]} r="7" fill="var(--gold-bg)" opacity="0.9" />
        <circle cx={style.spot[0]} cy={style.spot[1]} r="13" fill="none" stroke="var(--gold-bg)" strokeWidth="1.5" opacity="0.5" />
      </svg>
      )}
      {children}
    </div>
  );
}

/** Formato da série (BO1/BO3), em Barlow normal: na condensada o O e o 0 ficam quase iguais. */
export function Fmt({ format, className }: { format: string; className?: string }) {
  return <span className={clsx("font-sans tracking-wide", className)}>{format.toUpperCase()}</span>;
}
