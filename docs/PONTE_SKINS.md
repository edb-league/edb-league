# Ponte de skins (site → servidor de CS2)

O site e a API ficam na nuvem; o MariaDB do WeaponPaints fica no PC do servidor. A ponte liga os dois sem abrir porta:

1. O jogador escolhe a skin no site. A API grava em `skin_selections` (Supabase).
2. `scripts/ponte_skins.py`, rodando no PC do servidor, pergunta à API "o que mudou?" (`GET /api/skins/bridge/changes`, com
   `Authorization: Bearer <BRIDGE_TOKEN>`) e grava no MariaDB. O jogador digita `!wp` no jogo.

## Configuração
- **API (Render):** variável `BRIDGE_TOKEN` com um texto aleatório longo. Sem ela o recurso fica desligado.
  Não defina `WP_DB_HOST` na API da nuvem (esse é o modo direto, só para rodar tudo na mesma máquina).
- **PC do servidor:** `pip install requests pymysql` e as variáveis `EDB_API_URL`, `BRIDGE_TOKEN`, `WP_DB_PASS`
  (e `WP_DB_HOST/PORT/NAME/USER` se diferirem do padrão), depois `python scripts/ponte_skins.py`.

## Limites desta versão
- O fluxo é do site para o jogo. Skin trocada dentro do jogo (`!wp`/`!skins`) não aparece no site.
- A ponte guarda até onde já aplicou em `ponte_skins.cursor`; apagar o arquivo reaplica todas as escolhas do site.
- As luvas gravam em `wp_player_gloves` (modelo) e `wp_player_skins` (pintura), como as facas.
