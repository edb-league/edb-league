# API EDB LEAGUE

API FastAPI que serve o frontend Next.js (`web/`). Ela reaproveita as regras Python do projeto
(`core.py`, `season_rankings.py`, `team_draw.py` e demais módulos da raiz) sem alterá-las. Os formatos
JSON estão em `web/src/lib/types.ts`; a lista de rotas está em `api/CONTRACT.md`.

## Rodar localmente

```bash
python -m venv .venv && source .venv/bin/activate      # fora do repositório, se preferir
pip install -r api/requirements-dev.txt

# Dados sintéticos, sem banco e sem chaves (ideal para desenvolver o frontend)
EDB_DEMO=1 XINXAS_ADMIN_PASSWORD=demo-senha-123 uvicorn api.main:app --port 8000

# Dados reais (Supabase)
SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... XINXAS_ADMIN_PASSWORD=... uvicorn api.main:app --port 8000
```

Abra `http://localhost:8000/docs` para a documentação interativa e `http://localhost:8000/api/health`
para o teste de saúde. Sem `SUPABASE_URL` e sem `EDB_DEMO`, a API usa o SQLite local do projeto.

## Testes

```bash
pytest -q
```

Os testes rodam sempre em modo demonstração ou com SQLite temporário e validam as respostas contra o
próprio `web/src/lib/types.ts`.

## Variáveis de ambiente

| Variável | Obrigatória | Para que serve |
|---|---|---|
| `SUPABASE_URL` | produção | URL do projeto Supabase. |
| `SUPABASE_SERVICE_ROLE_KEY` | produção | Chave de serviço. Fica só no servidor, nunca no frontend. |
| `XINXAS_ADMIN_PASSWORD` | para usar a Administração | Senha do admin. A Administração fica bloqueada se estiver vazia ou igual a `SUBSTITUA-POR-UMA-SENHA-FORTE`. |
| `EDB_SESSION_SECRET` | recomendada | Segredo que assina o cookie `edb_admin`. Sem ele, é derivado da senha. Use um valor longo e aleatório. |
| `EDB_ALLOWED_ORIGINS` | produção | Origens permitidas (CORS e verificação de `Origin`), separadas por vírgula. Padrão `http://localhost:3000`. Ex.: `https://edb-league.vercel.app`. |
| `EDB_COOKIE_SECURE` | produção | `1` marca o cookie como `Secure`. Obrigatório com HTTPS. |
| `EDB_TRUST_PROXY` | atrás de proxy | `1` usa `X-Forwarded-For` para o limite de tentativas de login por IP. Ligue só se o proxy for confiável. |
| `STEAM_API_KEY` | opcional | Avatar e horas de jogo na página do jogador. |
| `EDB_DEMO` | desenvolvimento | `1` usa dados sintéticos em memória. |
| `EDB_TODAY` | testes | Data fixa `AAAA-MM-DD` para simular o calendário. |
| `PORT` | container | Porta do servidor (Docker, Render e Fly já definem). |

## Segurança

- Rotas públicas são somente leitura e não expõem `steamid`.
- A Administração usa cookie `edb_admin` assinado (HMAC), `HttpOnly`, `SameSite=Lax`, validade de 8 horas.
- Máximo de 5 tentativas de login por IP em 15 minutos (memória do processo; com mais de uma instância o
  limite vale por instância).
- Rotas que alteram dados rejeitam `Origin` fora de `EDB_ALLOWED_ORIGINS`.
- Em produção o frontend chama `/api/*` no mesmo domínio (rewrite do Next.js), então o cookie é de primeira parte.

## Deploy

A imagem precisa dos módulos Python da raiz, por isso o build parte da **raiz do repositório**:

```bash
docker build -f api/Dockerfile -t edb-api .
docker run --rm -p 8000:8000 -e EDB_DEMO=1 -e XINXAS_ADMIN_PASSWORD=demo-senha-123 edb-api
```

### Render

1. Novo **Web Service** a partir do repositório, ambiente **Docker**.
2. Dockerfile path: `api/Dockerfile`. Docker build context directory: `.` (raiz).
3. Health check path: `/api/health`.
4. Em Environment, defina `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `XINXAS_ADMIN_PASSWORD`,
   `EDB_SESSION_SECRET`, `EDB_ALLOWED_ORIGINS` (domínio do frontend), `EDB_COOKIE_SECURE=1`,
   `EDB_TRUST_PROXY=1` e, se quiser, `STEAM_API_KEY`.
5. No plano gratuito o serviço hiberna; a primeira requisição depois disso demora alguns segundos.

### Fly.io

```bash
fly launch --no-deploy --dockerfile api/Dockerfile --internal-port 8000   # a partir da raiz do repositório
fly secrets set SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... XINXAS_ADMIN_PASSWORD=... \
  EDB_SESSION_SECRET=... EDB_ALLOWED_ORIGINS=https://seu-frontend.vercel.app
fly deploy
```

No `fly.toml`, use `[env] EDB_COOKIE_SECURE = "1"` e `EDB_TRUST_PROXY = "1"`, e um check HTTP em `/api/health`.

### Ligando o frontend

No Vercel, aponte o rewrite do Next.js (`/api/:path*`) para a URL pública da API, por exemplo
`https://edb-api.onrender.com/api/:path*`, e inclua o domínio do frontend em `EDB_ALLOWED_ORIGINS`.

## Cache

O servidor guarda um retrato dos dados por 60 segundos (invalidado a cada escrita administrativa). Respostas
públicas saem com `Cache-Control: public, s-maxage=30, stale-while-revalidate=60`; as demais, `no-store`.
O calendário (`ensure_edb_calendar`) é conferido no máximo uma vez por hora.
