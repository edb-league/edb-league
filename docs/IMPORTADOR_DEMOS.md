# Importador de demos (.dem)

Lê a pasta de demos no próprio computador, extrai as estatísticas e envia só o resultado ao Supabase.
A demo nunca sobe (o limite do Storage gratuito é 50 MB por arquivo e a demo tem ~230 MB).

## Nome do arquivo

`md3_inferno_20_10_1.dem`  =  formato, mapa, dia, mês, ordem.

| Parte | Regra |
|---|---|
| `md3` / `md1` | Formato da série. |
| mapa | Conferido com o mapa dentro da demo. Se divergir, a série não é importada. |
| `dd_mm` | Data. O ano é o atual (data futura cai no ano anterior). |
| ordem | md3: obrigatório, 1 a 3, na ordem em que os mapas foram jogados. md1: opcional (só para duas md1 no mesmo dia). |

Também valem `.dem.gz` e `.gz` (o arquivo compactado com gzip, como `md1_inferno_19_10.gz`). Arquivo com outra extensão aparece como ignorado. Uma md3 só é gravada com os três mapas e o mesmo elenco de dez jogadores nos três.

## Instalação (uma vez)

Python 3.11 ou mais novo. Na raiz do repositório:

    pip install demoparser2 pandas requests

Crie o arquivo `.env` na raiz do repositório (o git já o ignora):

    SUPABASE_URL=https://cgopqcbgxpzurejtjmbu.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=<chave service_role do projeto>

A chave service_role fica só neste arquivo. Nunca vai para o site, para o git nem para o chat.

## Uso

    python scripts/edb_import.py                       # prévia: não grava nada
    python scripts/edb_import.py --gravar              # mostra a prévia e pergunta antes de gravar cada série
    python scripts/edb_import.py --gravar --sim        # grava sem perguntar, só séries sem pendência
    python scripts/edb_import.py --vigiar --gravar --sim   # fica olhando a pasta (a cada 60 s)

Pasta padrão: `C:\Users\Usuario\Documents\Demos EDB` (troque com `--pasta` ou `EDB_DEMOS_DIR`).
A primeira leitura de cada demo leva alguns minutos; o resultado fica em `.edb_cache` dentro da pasta.

## O que ele faz

1. Ignora arquivos ainda sendo copiados (mexidos há menos de 20 s) e nomes fora do padrão (avisa).
2. Calcula o SHA-256 e pula demos já importadas (o hash fica em `matches.notes`).
3. Processa a demo (round faca fora, regras validadas contra o SCOPE) e confere mapa, 10 jogadores e placar.
4. Agrupa md3 por data e elenco. Série incompleta ou com erro não é gravada.
5. Identifica jogadores pelo SteamID. Sem SteamID cadastrado:
   - nick igual ao de um jogador sem SteamID (ex.: VnD): sugere o vínculo (com `--sim`, vincula sozinho);
   - qualquer outro caso: pergunta qual jogador é (ou cria um novo). Com `--sim`, a série fica pendente.
6. Grava `matches`, `player_stats`, `player_match_detail`, `player_scope_stats` (só utilitários) e chama
   `register_edb_confronto`, que cria a série, os times e o vencedor. Se algo falhar, desfaz o que gravou.
7. IDs no padrão `edb-t1-bo3-02-mirage`; a temporada vem da data (precisa estar aberta).

## Times PT e PL

PT é o time em que joga o Neteb (nick de demo "Петэв", jogador Pyetev) e PL é o time em que joga o The Most (Scby).
A regra vale mapa a mapa, nesta ordem:
1. Pyetev e Scby no mesmo time: esse time é PT;
2. só o Pyetev joga: o time dele é PT;
3. só o Scby joga: o time oposto é PT;
4. nenhum dos dois joga: vale o time com mais jogadores do PT do mapa anterior (no primeiro mapa, quem começou de T).

Para mudar: `--ancora-pt Fulano` e `--ancora-pl Ciclano`. `--trocar-times` inverte depois das âncoras.
A prévia sempre mostra em que se baseou a escolha.

## Substituições na BO3

Jogadores podem entrar e sair entre os mapas. As demos md3 do mesmo dia com ordens 1, 2 e 3 formam uma série mesmo
com elenco diferente; a prévia mostra quem entrou e quem saiu em cada mapa e avisa se menos de 6 jogadores se repetem
de um mapa para o outro. Ninguém pode jogar pelos dois times na mesma série.
Para gravar série com substituição, o banco precisa da migração `db/migrations/20261021_confronto_com_substituicoes.sql`
(testada em `db/tests/`). Sem ela, a série é recusada pelo banco e desfeita, com aviso na tela.

## Partidas que já estão no banco

Antes de gravar, o importador procura no banco um mapa igual, com os mesmos 10 jogadores e data a até 1 dia de
distância. Se achar (por exemplo, partida cadastrada pelos prints do SCOPE), não cria outra partida.

- Se a partida existe **sem** os dados da demo, o importador oferece gravar só os detalhes da demo nela
  (`player_match_detail`) e guarda o hash da demo nas notas. Placar, times, série e estatísticas já cadastradas
  não mudam. Se algo falhar, os detalhes recém-gravados são removidos.
- Se a partida já tem os dados da demo, avisa e não faz nada.
- Se só parte de uma série existe no banco, não grava, para não duplicar.

## Rating e campos que a demo não tem

`rating` gravado é o Rating 2.0 estimado (fórmula pública da HLTV). Mira, 1ª bala, tempo até matar e ADR oficial
do SCOPE ficam vazios nas partidas importadas de demo.
