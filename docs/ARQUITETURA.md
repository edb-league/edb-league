# EDB LEAGUE: estrutura, frontend e API

O app Streamlit continua funcionando. O novo site é um frontend próprio (Next.js) que consome uma API (FastAPI)
construída sobre o mesmo pacote Python de regras (`packages/edb`), compartilhado com o Streamlit.

## Estrutura do repositório

```
apps/
  streamlit/    app Streamlit (app.py, telas, estilos, assets/, tests/)
  api/          API FastAPI (edb_api/), Dockerfile, CONTRACT.md, tests/
  web/          frontend Next.js, testes Playwright e axe
packages/
  edb/          regras e dados: core, season_rankings, season_system, storage, demo_importer, team_draw...
db/             supabase_schema.sql e migrations/
docs/           ARQUITETURA, PUBLICAR, REGULAMENTO
scripts/        inspect_demo.py
.streamlit/     configuração e secrets do Streamlit
app.py          entrada de compatibilidade para a hospedagem do Streamlit
requirements.txt  dependências do app Streamlit
pytest.ini      testes de todo o repositório
```

Dependências entre as partes: `apps/streamlit` e `apps/api` importam `edb`; `edb` não importa nenhum dos dois.
`.streamlit/`, `requirements.txt` e `app.py` ficam na raiz porque a hospedagem do Streamlit procura por eles ali.

```
Navegador ──► Next.js (apps/web)  ── /api/* (rewrite, mesma origem) ──►  FastAPI (apps/api)  ──►  Supabase
              Vercel                                                  Render ou Fly        (ou SQLite local)
                                                                      reusa packages/edb (core, season_rankings,
                                                                      season_system, bagres etc.)
```

## Decisões

| Tema | Decisão | Motivo |
|---|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind 4, Radix Tabs | Controle total do HTML e da acessibilidade, sem CSS por cima do Streamlit. |
| Backend | FastAPI reaproveitando os módulos Python | A regra de negócio (rankings, temporadas, sorteio) não é reescrita nem duplicada. |
| Contrato | `apps/web/src/lib/types.ts` | Os testes da API leem esse arquivo e falham se faltar ou sobrar campo. |
| Cookie do admin | Mesma origem via rewrite `/api/*` | Cookie de primeira parte, sem CORS e sem `SameSite=None`. |
| Fonte | Atkinson Hyperlegible Next, hospedada junto do site | Feita para leitura clara, sem pedir nada ao Google Fonts. |
| Sem esqueleto de carregamento | Sem `loading.tsx` | O HTML chega completo. Funciona sem JavaScript e devolve 404 real em páginas inexistentes. |

## Mapa de telas

| Streamlit | Novo site |
|---|---|
| Visão geral e sorteador | `/` |
| Rankings | `/rankings/elite`, `/superacao`, `/xp`, `/bagres` |
| Missões e XP | `/missoes-xp` |
| Partidas BO1/BO3 e mapa | `/partidas`, `/partidas/mapa/[id]` |
| Jogadores e perfil | `/jogadores`, `/jogadores/[id]` |
| Comparar | `/comparar` (formulário GET, funciona sem JavaScript) |
| Hall da Fama, Medalhas | `/hall-da-fama`, `/medalhas` |
| Administração | `/admin` (elenco, importar, confrontos, temporadas, exportar CSV) |

Links antigos (`?page=`, `?player=`, `?match=`, `?bo3=`, `?ranking=`, `?season=`) redirecionam com 308 em `apps/web/src/proxy.ts`.

## Acessibilidade

- Contraste: `npm run check:contrast` valida 72 pares de cores (claro e escuro) contra WCAG AA. Tokens em `src/app/tokens.css`.
- Resultado nunca depende só de cor: vitória e derrota têm ícone e texto, times têm letra e forma.
- Link para pular ao conteúdo, `aria-current`, landmarks com nome, foco de 3 px, alvos de 44 px, `prefers-reduced-motion`, modo de alto contraste do sistema.
- Tema automático, claro ou escuro, sem piscar no carregamento.
- Gráficos são listas e tabelas, com SVG apenas como reforço.
- Testes: `npm run test:e2e` roda axe (WCAG 2.0, 2.1 e 2.2, A e AA) em todas as páginas, nos dois temas, mais teclado, 320 px sem rolagem horizontal, zoom, sem JavaScript e fluxo do admin. Hoje: 44 de 44 passando.

Isso cobre o que se verifica por máquina. Falta uma passada manual com leitor de tela (NVDA, VoiceOver) antes de divulgar.

## Segurança da administração

Senha em `XINXAS_ADMIN_PASSWORD`, comparação em tempo constante, 5 tentativas por IP em 15 minutos, cookie `edb_admin` assinado
(HMAC), `HttpOnly`, `SameSite=Lax`, 8 horas, verificação de `Origin` nas rotas que gravam. As chaves do Supabase e da Steam ficam só na API.
Detalhes em `apps/api/README.md` e `apps/api/CONTRACT.md`.

## Rodar localmente

```bash
# 1. API com dados sintéticos
pip install -r apps/api/requirements-dev.txt
EDB_DEMO=1 XINXAS_ADMIN_PASSWORD=demo-senha-123 uvicorn --app-dir apps/api edb_api.main:app --port 8000

# 2. Site
cd apps/web && cp .env.example .env.local && npm install && npm run dev

# 3. App Streamlit (opcional), a partir da raiz
streamlit run apps/streamlit/app.py
```

Abra http://localhost:3000. Com `EDB_DEMO=1` aparece um aviso fixo de dados fictícios.
Verificações: `npm run typecheck`, `npm run lint`, `npm run check:contrast`, `npm run test:e2e` (em `apps/web`) e `python -m pytest -q` na raiz.

## Publicação

1. **API (Render ou Fly):** passos e variáveis em `apps/api/README.md`. Defina `EDB_ALLOWED_ORIGINS` com o endereço do site e `EDB_COOKIE_SECURE=1`.
2. **Site (Vercel):** projeto com Root Directory `apps/web`. Variáveis: `API_URL` (endereço público da API) e `NEXT_PUBLIC_SITE_URL`.
3. **Virada:** mantenha o Streamlit no ar durante alguns dias, compare números lado a lado, depois aponte o domínio para o Vercel.

## Limites conhecidos

- **Supabase real não foi testado.** Confronto BO1/BO3 e homologação usam as funções `register_edb_confronto`, `homologate_edb_season`
  e `ensure_edb_calendar`, que só existem no banco ao vivo e não estão no `supabase_schema.sql` do repositório. Os testes usam um
  simulador. Faça o primeiro teste com um confronto de verdade e confira no Streamlit.
- **Upload de `.dem` pelo Vercel.** Demos são grandes e o upload passa pelo rewrite `/api`. Não verifiquei o limite de corpo desse
  caminho no Vercel. Se falhar com arquivos reais, use o placar em CSV ou coloque site e API em subdomínios do mesmo domínio e
  envie direto à API.
- **Modo SQLite local** não tem tabelas de BO3 e temporadas; a API usa o calendário padrão e dados de confronto vazios.
- **Limite de tentativas de login** vale por instância da API. Com uma instância, como no plano gratuito, é exato.
- **Render gratuito hiberna.** A primeira visita depois de um tempo parado demora alguns segundos.
- A imagem Docker da API não foi construída aqui (sem Docker no ambiente). O `apps/api/Dockerfile` está pronto para o primeiro build.
