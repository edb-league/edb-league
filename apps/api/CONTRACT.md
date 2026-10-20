# Contrato da API EDB LEAGUE

Os formatos JSON estão em `apps/web/src/lib/types.ts` (fonte de verdade). A API não altera o pacote
compartilhado `edb` (`core`, `season_rankings` etc.); apenas o importa.

Todas as rotas começam com `/api`. Erros: `{ "detail": "mensagem em português" }`.

## Públicas (somente leitura, sem autenticação)

| Método | Rota | Resposta |
|---|---|---|
| GET | `/api/health` | `{ ok: true }` |
| GET | `/api/meta` | `Meta` |
| GET | `/api/home?season=N` | `Home` |
| GET | `/api/rankings/{elite\|superacao\|xp\|bagres}?season=N` | `Ranking` |
| GET | `/api/missions?season=N` | `Missions` |
| GET | `/api/players?include_inactive=false` | `PlayerListItem[]` |
| GET | `/api/players/{id}` | `PlayerDetail` (inativo também abre, como no Streamlit) |
| GET | `/api/compare?a=ID&b=ID` | `Compare` (400 se iguais) |
| GET | `/api/hall-of-fame` | `Hall` |
| GET | `/api/medals` | `MedalCatalogue` |
| GET | `/api/matches?season=N` | `MatchesList` |
| GET | `/api/matches/{match_id}` | `MatchDetail` |
| POST | `/api/draw` body `{ player_ids: string[10] }` | `DrawResult` |

`season` omitido = temporada vigente (`chosen_season_number`). Respostas públicas levam
`Cache-Control: public, s-maxage=30, stale-while-revalidate=60`.

## Administração (cookie httpOnly assinado)

| Método | Rota | Corpo / Resposta |
|---|---|---|
| GET | `/api/admin/session` | `AdminSession` |
| POST | `/api/admin/login` | `{ password }` → `{ ok: true }` e Set-Cookie `edb_admin` |
| POST | `/api/admin/logout` | `{ ok: true }` |
| GET | `/api/admin/overview` | `AdminOverview` |
| POST | `/api/admin/players` | `{ nickname, steamid?, skill_level }` → `AdminPlayer` |
| PATCH | `/api/admin/players/{id}` | `{ nickname?, steamid?, skill_level? }` → `AdminPlayer` |
| POST | `/api/admin/players/{id}/archive` | `AdminPlayer` |
| POST | `/api/admin/players/{id}/reactivate` | `AdminPlayer` |
| POST | `/api/admin/seasons/{n}/homologate` | `{ ok: true }` (só nuvem; mesma lógica do app.py) |
| GET | `/api/admin/confront/candidates?season=N` | `ConfrontCandidates` |
| POST | `/api/admin/confront` | `ConfrontRequest` → `{ ok: true }` (só nuvem; RPC `register_edb_confronto`) |
| POST | `/api/admin/import/preview` | multipart: `method` = `demo` \| `csv` \| `sample`, `file` → `ImportPreview` |
| POST | `/api/admin/import/commit` | `ImportCommit` → `{ ok: true, match_id }` |
| GET | `/api/admin/export/{players\|matches\|stats}.csv` | CSV UTF-8 com BOM |

### Segurança do admin
- Senha vem de `XINXAS_ADMIN_PASSWORD` (mesmo segredo do Streamlit). Bloqueado se vazia ou igual a
  `SUBSTITUA-POR-UMA-SENHA-FORTE`.
- Comparação com `hmac.compare_digest`. Limite de 5 tentativas por IP em 15 min (memória do processo).
- Cookie `edb_admin`: token `expiry.assinatura` (HMAC-SHA256 com `EDB_SESSION_SECRET`, ou derivado da
  senha se ausente), validade 8 h, `HttpOnly`, `SameSite=Lax`, `Secure` quando `EDB_COOKIE_SECURE=1`.
- Rotas POST/PATCH validam o cabeçalho `Origin` contra `EDB_ALLOWED_ORIGINS` (lista separada por vírgula;
  padrão `http://localhost:3000`). O frontend usa proxy same-origin (`/api/*` reescrito pelo Next).
- Chaves do Supabase e da Steam nunca saem do servidor.

## Variáveis de ambiente
`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `XINXAS_ADMIN_PASSWORD`, `STEAM_API_KEY`,
`EDB_SESSION_SECRET`, `EDB_ALLOWED_ORIGINS`, `EDB_COOKIE_SECURE`, `EDB_DEMO` (1 = dados sintéticos).

## Modo demonstração (`EDB_DEMO=1`)
Snapshot sintético em memória (jogadores fictícios, BO1/BO3, estrelas congeladas, títulos), usado
nos testes e no desenvolvimento do frontend. `Meta.demo` fica `true`. Escritas administrativas
funcionam sobre o snapshot em memória.
