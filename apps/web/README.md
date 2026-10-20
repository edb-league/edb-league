# EDB LEAGUE, frontend

Next.js 16 (App Router), React 19, TypeScript, Tailwind 4. Consome a API da pasta `../api`.
Visão geral, decisões e publicação: `../docs/ARQUITETURA.md`.

## Começar

```bash
cp .env.example .env.local     # API_URL aponta para a API (padrão http://127.0.0.1:8000)
npm install
npm run dev                    # http://localhost:3000
```

Precisa da API no ar. Para desenvolver sem banco: `EDB_DEMO=1 XINXAS_ADMIN_PASSWORD=demo-senha-123 uvicorn api.main:app --port 8000`
na raiz do repositório.

## Scripts

| Comando | O que faz |
|---|---|
| `npm run typecheck` | TypeScript sem emitir arquivos |
| `npm run lint` | ESLint (regras do Next e do React) |
| `npm run check:contrast` | Confere os pares de cor de `src/app/tokens.css` contra WCAG AA |
| `npm run test:e2e` | Playwright com axe, teclado, responsivo e fluxo do admin |
| `npm run build` e `npm start` | Build e servidor de produção |

O `test:e2e` sobe a API em modo demonstração e o site sozinho, ou reaproveita servidores que já estejam no ar.
Se o Chromium do Playwright não estiver instalado, use `PW_CHROMIUM_PATH=/caminho/do/chrome npm run test:e2e`.

## Estrutura

```
src/app/            rotas (páginas são componentes de servidor; admin é cliente)
src/app/tokens.css  cores e espaçamentos, com claro e escuro por light-dark()
src/components/ui/  Button, Card, Field, Table, Tabs, Charts, Notice, PageHeader
src/components/admin/  abas da Administração
src/lib/types.ts    contrato JSON com a API (fonte da verdade)
src/proxy.ts        redirecionamento dos links antigos do Streamlit
e2e/                testes Playwright
```

## Regras de projeto

- Cor nunca é a única pista: resultado tem ícone e texto, times têm letra e forma.
- Toda cor sai de `tokens.css`. Ao mudar um token, rode `npm run check:contrast`.
- Campos usam `Field`/`TextField`/`SelectField`, que ligam rótulo, dica e erro por `id`.
- Tabelas usam `TableWrap` (região rolável focável com legenda).
- Não adicione `loading.tsx`: o conteúdo deve chegar no HTML inicial (funciona sem JavaScript e mantém o status 404 correto).
