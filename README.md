# EDB LEAGUE

Site da liga informal de Counter-Strike 2: perfis, rankings **Elite / Superação / XP**, missões, medalhas, histórico de
partidas, sorteador de times e administração (elenco, importação de demos, confrontos e homologação de temporada).

- **Site:** `apps/web` (Next.js, Vercel)
- **API:** `apps/api` (FastAPI, Render)
- **Regras e cálculos:** `packages/edb` (Python, compartilhado pela API e pelo importador)
- **Banco:** Supabase (`db/`), ou SQLite local para testes

Visão geral, publicação e limites conhecidos: [docs/ARQUITETURA.md](docs/ARQUITETURA.md).
Regulamento: [docs/REGULAMENTO.md](docs/REGULAMENTO.md). Importação de demos: [docs/IMPORTADOR_DEMOS.md](docs/IMPORTADOR_DEMOS.md).

## Rodar no computador

Python 3.11 ou 3.12 e Node 22.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r apps/api/requirements-dev.txt

# API com dados fictícios
$env:EDB_DEMO = "1"; $env:XINXAS_ADMIN_PASSWORD = "demo-senha-123"
python -m uvicorn --app-dir apps/api edb_api.main:app --port 8000

# Site (em outro terminal)
cd apps/web
copy .env.example .env.local
npm install
npm run dev
```

Abra <http://localhost:3000>. Variáveis da API e do login com a Steam: [apps/api/README.md](apps/api/README.md).

## Temporadas e regras

- **Temporada 0 (experimental):** encerrada em 18/10/2026; as duas BO3 reais ficam no banco e não são recalculadas.
- **Temporada 1:** 15/10/2026 (primeira partida da liga) a 18/11/2026; as seguintes são mensais, do dia 19 ao dia 18.
- **Elite:** 6 melhores mapas por Índice Elite (KPR e ADR). **Superação:** 6 melhores mapas pela superação da meta das
  estrelas congeladas. **XP:** 6 mapas (40 por participação, 20 por vitória) e 100 XP por semana de missão.
- São necessários ao menos 6 mapas para concorrer a um título (MVP, Revelação e Xinxa). Depois do encerramento, o
  administrador confere e homologa; o banco grava os snapshots.

## Testes e verificações

```powershell
python -m pytest -q          # regras, API e importador (na raiz)
cd apps/web
npm run typecheck; npm run lint; npm run check:contrast
npm run test:e2e             # navegador: acessibilidade (axe), navegação, 320 px, administração
```

Os testes da API usam um simulador do Supabase; confronto e homologação reais só existem no banco ao vivo.

## Estrutura

```text
apps/api/       API FastAPI (edb_api/), Dockerfile, CONTRACT.md, tests/
apps/web/       frontend Next.js e testes Playwright
packages/edb/   regras: core, season_rankings, season_system, storage, demo_stats, demo_pipeline, team_draw...
db/             supabase_schema.sql e migrations/
docs/           ARQUITETURA, IMPORTADOR_DEMOS, REGULAMENTO
scripts/        edb_import.py (importador local) e inspect_demo.py (testar uma demo pelo terminal)
```

`edb` não importa a API nem o site. Para ler uma demo no terminal: `python scripts/inspect_demo.py sua_partida.dem`.
