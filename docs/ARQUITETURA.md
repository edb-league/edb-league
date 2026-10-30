# EDB LEAGUE: estrutura, frontend e API

O site é um frontend próprio (Next.js) que consome uma API (FastAPI) construída sobre o pacote Python de regras
(`packages/edb`). O app Streamlit antigo foi aposentado e está no histórico do git.

## Estrutura do repositório

```
apps/
  api/          API FastAPI (edb_api/), Dockerfile, CONTRACT.md, tests/
  web/          frontend Next.js, testes Playwright e axe
packages/
  edb/          regras e dados: core, season_rankings, season_system, storage, demo_importer, team_draw...
db/             supabase_schema.sql e migrations/
docs/           ARQUITETURA, IMPORTADOR_DEMOS, REGULAMENTO
scripts/        edb_import.py (importador local), inspect_demo.py
requirements.txt  dependências para rodar as regras e o importador no computador
pytest.ini      testes de todo o repositório
```

Dependências entre as partes: `apps/api` importa `edb`; `edb` não importa a API.

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
| Fonte | Barlow e Barlow Condensed (`@fontsource`), hospedadas junto do site | Sem pedir nada ao Google Fonts. Importadas em `layout.tsx` para o Next resolver os pacotes. |
| Sem esqueleto de carregamento | Sem `loading.tsx` | O HTML chega completo. Funciona sem JavaScript e devolve 404 real em páginas inexistentes. |

## Mapa de telas

| Streamlit | Novo site |
|---|---|
| Visão geral | `/` (hero, destaques, Elite, últimas partidas, atalhos) |
| Sorteador | `/sorteador` |
| Regras (antes na visão geral) | `/regulamento` |
| Rankings | `/rankings/elite`, `/superacao`, `/xp`, `/bagres` (abas Elite, Superação, XP e BAGRES) |
| Missões e XP | `/missoes-xp` (grupo Conquistas) |
| Partidas BO1/BO3 e mapa | `/partidas`, `/partidas/mapa/[id]` |
| Jogadores e perfil | `/jogadores`, `/jogadores/[id]` (abas por `?aba=`: resumo, estatisticas, partidas, medalhas) |
| Comparar | `/comparar` (formulário GET, funciona sem JavaScript) |
| Hall da Fama, Medalhas | `/hall-da-fama`, `/medalhas` (grupo Conquistas, com barra de abas; Medalhas filtra por `?faixa=`) |
| Administração | `/admin` (elenco, importar, confrontos, temporadas, exportar CSV) |

## Estatísticas das demos (estilo HLTV)

A aba **Estatísticas** do jogador segue as seções da página de jogador da HLTV: Rating, notas de 0 a 100, Poder de fogo,
Entrada, Trocas, Abertura, Fechamento, Sniper e Utilitários, mais multi-kills, clutches, armas, mapas, companheiros,
adversários e jogadores parecidos.

- **Origem:** o arquivo `.dem`. `packages/edb/edb/demo_stats.py` lê a demo e devolve contagens por jogador e partida
  (`analyze`). A partida começa no último `begin_new_match`, então o round faca e o warmup não contam.
- **Armazenamento:** tabela `player_match_detail` (migração `db/migrations/20261020_player_match_detail.sql`), só contagens.
  É aditiva: não altera `player_stats` nem `player_scope_stats`. Partida sem linha nessa tabela simplesmente não entra.
- **Cálculo:** `packages/edb/edb/hltv_stats.py` transforma as contagens em taxas (KPR, rating, percentuais). Não acessa banco.
- **Tela:** `GET /api/players/{id}` devolve o bloco `advanced` (`null` sem demo). Componente `AdvancedStats.tsx`.

O que é igual à HLTV: Rating 1.0 (fórmula pública, conferida com os totais do FalleN: 1,03), KPR, DPR, ADR, KAST, multi-kill,
aberturas, clutches, proporção de sniper e AWP. O que é adaptado aparece com a marca "adaptado" na tela: Rating 2.0
(estimativa, fica perto do rating do SCOPE), dano por round vencido (no lugar do Round Win Shares) e vivo após o plant.
Rating 3.0 e Round Swing não são públicos e não são calculados. As notas de 0 a 100 comparam o jogador com os outros da
liga, não com a cena profissional, e só aparecem com 3 jogadores ou mais com demo.

Diferenças conhecidas contra o SCOPE (3 partidas): kills, mortes, assistências, aberturas, flashes, granadas e smokes batem
exatamente; o dano da demo fica cerca de 1% abaixo, o KAST pode diferir em 1 ponto e há casos com 1 trade a menos.

## Banners e espaço na tela

- Cada página de topo usa `PageHeader` (`components/ui/PageHeader.tsx`) com arte de fundo e a barra de temporada embutida. A altura fica perto de 215 px no computador.
- Para trocar uma imagem, substitua o arquivo em `apps/web/public/art/` mantendo o nome (`home`, `rankings`, `matches`, `duel`, `trophy`, `medals`, `xp`, todos `.webp`). Uma camada sólida fica por cima do texto, então o contraste não depende da imagem.
- Jogadores, Regulamento e Sorteador ainda não têm arte. Para dar uma, inclua um nome em `ArtName` e passe `art="nome"` no `PageHeader` da página.
- Regras de espaço: cada dado aparece uma vez por tela. Detalhes longos ficam em `<details>` (gráfico de Comparar, mapas antigos em Partidas, perguntas do Regulamento).

Links antigos (`?page=`, `?player=`, `?match=`, `?bo3=`, `?ranking=`, `?season=`) redirecionam com 308 em `apps/web/src/proxy.ts`.

## Acessibilidade

- Contraste: `npm run check:contrast` valida 100 verificações de cores (claro e escuro) contra WCAG AA. Tokens em `src/app/tokens.css`.
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
```

Abra http://localhost:3000. Com `EDB_DEMO=1` aparece um aviso fixo de dados fictícios.
Verificações: `npm run typecheck`, `npm run lint`, `npm run check:contrast`, `npm run test:e2e` (em `apps/web`) e `python -m pytest -q` na raiz.

## Publicação

1. **API (Render ou Fly):** passos e variáveis em `apps/api/README.md`. Defina `EDB_ALLOWED_ORIGINS` com o endereço do site e `EDB_COOKIE_SECURE=1`.
2. **Site (Vercel):** projeto com Root Directory `apps/web`. Variáveis: `API_URL` (endereço público da API) e `NEXT_PUBLIC_SITE_URL`.

## Votação de MVP da partida

Quem jogou o mapa e entrou com a Steam vota em outro jogador do mesmo mapa (um voto, que pode ser trocado). A votação fica aberta por 7 dias depois do mapa (`EDB_MVP_VOTE_DAYS` muda isso) ou até todos votarem; só então o resultado aparece, sem mostrar quem votou em quem. É um reconhecimento: não entra em ranking, XP ou título. Exige a tabela `match_mvp_votes` (`db/migrations/20261030_votacao_mvp.sql`); sem ela, ou com o banco local, o bloco simplesmente não aparece e o resto do site segue normal.

## Privacidade e avisos

- **Escolhas do jogador** (`/privacidade`): quem entrou com a Steam pode esconder a foto, o nome na Steam e as horas de CS do próprio perfil. O padrão é mostrar, como antes, e o SteamID nunca aparece para ninguém. As escolhas ficam na tabela `player_privacy` (`db/migrations/20261030_privacidade_jogador.sql`); sem ela, a página mostra que as opções ainda não estão disponíveis. As fotos usam cache de até 10 minutos no site.
- **Avisos no Discord** (opcional): com `EDB_DISCORD_WEBHOOK_URL`, a API posta quando uma série ou partida é registrada e quando uma temporada é homologada. O envio roda em segundo plano, nunca marca ninguém (`allowed_mentions` vazio) e uma falha só vai para o log, sem impedir o registro.

## Linha do tempo dos rounds

O parser (versão 4) registra, para cada round, quem venceu, o lado, o motivo (eliminação, bomba, desarme ou tempo), se a bomba foi plantada e o placar acumulado. A importação grava isso na tabela `match_rounds` (`db/migrations/20261030_linha_do_tempo_rounds.sql`) depois do confronto, em termos do time A (esquerda) e B (direita) da série, e a página da partida mostra uma coluna por round. É um extra: se a tabela não existir, a série é gravada do mesmo jeito (com um aviso no log) e a página não mostra o bloco. O motivo vem dos eventos da demo (bomba plantada/desarmada); quando eles não bastam, o texto do jogo desempata e, sem ele, o round fica sem motivo em vez de um palpite. Mapas importados antes da versão 4 não têm linha do tempo.

## Limites conhecidos

- **Supabase real não foi testado.** Confronto BO1/BO3 e homologação usam as funções `register_edb_confronto`, `homologate_edb_season`
  e `ensure_edb_calendar`, que só existem no banco ao vivo e não estão no `supabase_schema.sql` do repositório. Os testes usam um
  simulador. Faça o primeiro teste com um confronto de verdade e confira os números no site.
- **Upload de `.dem` pelo Vercel.** Demos são grandes e o upload passa pelo rewrite `/api`. Não verifiquei o limite de corpo desse
  caminho no Vercel. Se falhar com arquivos reais, use o placar em CSV ou coloque site e API em subdomínios do mesmo domínio e
  envie direto à API.
- **Modo SQLite local** não tem tabelas de BO3 e temporadas; a API usa o calendário padrão e dados de confronto vazios.
- **Limite de tentativas de login** vale por instância da API. Com uma instância, como no plano gratuito, é exato.
- **Render gratuito hiberna.** Sem requisições por ~15 min, a primeira visita espera a API subir. O workflow `keepalive.yml` chama `/api/health` a cada 10 min (pelo site) para evitar isso, e o site tenta de novo até 2 vezes quando a API responde 502/503/504. Se o repositório ficar 60 dias sem atividade, o GitHub pausa o agendamento.
- A imagem Docker da API não foi construída aqui (sem Docker no ambiente). O `apps/api/Dockerfile` está pronto para o primeiro build.

### Importação automática

Ver `docs/IMPORTADOR_DEMOS.md` (`scripts/edb_import.py`, módulo `edb.demo_pipeline`).
