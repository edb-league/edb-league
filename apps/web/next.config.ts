import type { NextConfig } from "next";

// URL interna da API FastAPI. No navegador, tudo passa por /api (mesma origem),
// o que dispensa CORS e permite cookie SameSite=Lax no login do administrador.
const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

const dev = process.env.NODE_ENV !== "production";

// Imagens das skins ficam no nosso Supabase Storage (bucket público "skins").
const SKINS_ORIGIN = new URL(
  process.env.SKINS_STORAGE_URL ?? "https://cgopqcbgxpzurejtjmbu.supabase.co/storage/v1/object/public/skins",
).origin;

// Política de conteúdo: o site só carrega o que é dele. As exceções são as fotos da Steam (imagens) e os
// scripts em linha que o Next usa para hidratar e que aplicam o tema antes da pintura.
const csp = [
  "default-src 'self'",
  `img-src 'self' data: https://*.steamstatic.com https://*.akamaihd.net ${SKINS_ORIGIN}`,
  "style-src 'self' 'unsafe-inline'",
  `script-src 'self' 'unsafe-inline'${dev ? " 'unsafe-eval'" : ""}`,
  "font-src 'self' data:",
  `connect-src 'self'${dev ? " ws:" : ""}`,
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  { key: "Strict-Transport-Security", value: "max-age=31536000" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
];

// Em desenvolvimento o Next só entrega os scripts do navegador para localhost. Para abrir o site pelo IP da rede
// (ex.: 192.168.1.33, necessário no login com a Steam), liste o endereço em DEV_ORIGINS, separado por vírgula.
const devOrigins = (process.env.DEV_ORIGINS ?? "").split(",").map((o) => o.trim()).filter(Boolean);

const nextConfig: NextConfig = {
  poweredByHeader: false,
  ...(devOrigins.length > 0 ? { allowedDevOrigins: devOrigins } : {}),
  reactStrictMode: true,
  images: {
    // Avatares da Steam (a API só devolve URLs https desses domínios).
    remotePatterns: [
      { protocol: "https", hostname: "**.steamstatic.com" },
      { protocol: "https", hostname: "**.akamaihd.net" },
    ],
  },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
