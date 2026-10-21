# EDB LEAGUE — aplicativo de CS2

Painel web para a liga informal de Counter-Strike 2. Possui perfis com estrelas,
rankings **Elite / Superação / XP**, missões, XP, histórico, premiações por
estatística, registro por CSV ou demo `.dem.gz` e exportação de backups.

**Status do desenvolvimento:** interface e regras implementadas; testes
automatizados das regras, do banco local e do importador com eventos simulados
passaram. A extração da demo REAL da xplay ainda precisa ser validada no
computador ou ambiente de hospedagem com `demoparser2` instalado. Não inventamos
Rating HLTV nem KAST: são exibidos somente quando fornecidos por outra fonte.

## A) Executar no computador (primeiro teste recomendado)

Instale o Python 3.11 ou 3.12. Baixe/descompacte esta pasta e execute no terminal:

### Windows (PowerShell)

```powershell
cd xinxas-league
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .streamlit\secrets.example.toml .streamlit\secrets.toml
# Edite .streamlit\secrets.toml e substitua a senha de exemplo.
streamlit run apps/streamlit/app.py
```

Caso o PowerShell não permita ativar ambientes virtuais, use diretamente
`.venv\Scripts\python.exe -m pip install -r requirements.txt` e
`.venv\Scripts\python.exe -m streamlit run apps/streamlit/app.py`.

### macOS / Linux

```bash
cd xinxas-league
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
# Edite .streamlit/secrets.toml e substitua a senha de exemplo.
streamlit run apps/streamlit/app.py
```

No navegador, abra o endereço local mostrado pelo Streamlit,
normalmente `http://localhost:8501`. A aba **Administração** exige a senha.
As demais abas são de visualização. Em execução local, os dados ficam em
`xinxas.db` (não incluído no ZIP), salvo se configurar Supabase.

## B) Testar com a partida enviada no chat

1. Abra **Administração** e entre com a senha.
2. Entre em **Importar demo / CSV**.
3. Para testar rapidamente o painel, selecione **Exemplo do print do SCOPE.GG**.
4. Clique **Carregar amostra do SCOPE.GG**. Confirme a **data real da partida**,
   os dados e o time vencedor, e depois **Confirmar e salvar partida**.
5. Os rankings, o histórico e o XP serão atualizados. O print contém dados
   reais transcritos da conversa; **rounds foram estimados pelo dano/ADR**.

Você também pode usar **Demo da xplay** e escolher a demo `.dem.gz` que
compartilhou na conversa (arquivo NÃO incluído no ZIP). Antes de salvar, confira
os 10 jogadores, kills, dano e rounds. A xplay pode gravar warmup, trocas de
jogadores e outros eventos que exigem ajustes na leitura.

Para inspecionar a demo sem abrir o painel:

```bash
python scripts/inspect_demo.py "sua_partida.dem.gz"
```

Se a leitura real apresentar valores diferentes do SCOPE.GG, compare os eventos
antes de contar a partida na liga. O ADR da demo deriva de `player_hurt` e pode
ser diferente da metodologia do SCOPE.GG; **o programa não calcula HLTV Rating
nem KAST da demo nesta versão.** O uploader limita os arquivos a 350 MB
compactados e a 1 GB descompactados.

## C) Publicar para o grupo com endereço web

Para que o link funcione para todos e os dados não desapareçam ao reiniciar,
**configure primeiro um banco persistente no Supabase**. SQLite é adequado aos
testes locais, mas o disco da hospedagem gratuita do Streamlit não garante
persistência dos dados inseridos ao longo do tempo.

1. Crie um projeto no [Supabase](https://supabase.com).
2. Em **SQL Editor**, execute o conteúdo de `db/supabase_schema.sql`. O SQL ativa
   Row Level Security e não cria políticas de acesso anônimo.
3. Localize a URL do projeto e a **chave `service_role`** (somente servidor).
   Não use a chave `anon`, e **nunca** publique a chave `service_role`.
4. Crie no [GitHub](https://github.com) um repositório, por exemplo,
   `xinxas-league`, e envie os arquivos desta pasta, **sem**
   `.streamlit/secrets.toml`, demos, senhas ou banco `.db`.
5. Acesse [Streamlit Community Cloud](https://share.streamlit.io), escolha
   **Create app**, selecione o repositório e o arquivo `apps/streamlit/app.py`.
6. Na área **Advanced settings → Secrets**, defina:

```toml
XINXAS_ADMIN_PASSWORD = "SENHA_FORTE_DE_VERDADE"
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "CHAVE_PRIVADA_SERVICE_ROLE"
```

7. Publique. Compartilhe o endereço `.streamlit.app` com o grupo. A leitura
   do painel é pública para quem tem o link; somente a aba Administração exige
   senha. O URL do app pode ser configurado na página do Streamlit.

**Atenção:** a hospedagem gratuita tem limites de recursos. A importação de demos
grande pode exceder memória/tempo; nesse caso, o parser pode rodar localmente e
o CSV resultante pode ser enviado pelo painel, ou optar por hospedagem mais forte.

## D) Temporadas e regras oficiais

O regulamento v1.0 esta em [docs/REGULAMENTO.md](docs/REGULAMENTO.md).

- **Temporada 0 (experimental):** encerrada em 18/10/2026; as duas BO3 reais permanecem no banco e seus resultados nao sao recalculados.
- **Temporada 1:** 19/10/2026 a 01/11/2026; ciclos sucessivos de 14 dias, sem limite de BO3.
- **Ranking Elite:** 6 melhores mapas por Indice Elite, usando KPR e ADR.
- **Ranking Superacao:** 6 melhores mapas por superacao da meta associada as estrelas congeladas na temporada.
- **Ranking XP:** 6 mapas (40 por participacao, 20 por vitoria) e ate 100 XP por semana de missao (2 semanas).
- Para concorrer a qualquer titulo oficial, sao necessarios ao menos 6 mapas disputados.
- **Tres titulos oficiais:** MVP (Elite), Revelacao (Superacao) e Xinxa (XP).
- Apos o encerramento, o administrador confere e homologa classificacoes e titulos. O banco grava snapshots historicos.
- Todos os mapas continuam computados no historico de carreira, mesmo que nao estejam entre os seis pontuaveis.
- A T0 conserva a metodologia legada sem receber novas regras retroativamente.
- O calendario quinzenal e as estrelas congeladas sao controlados automaticamente no Supabase. Alteracoes de estrelas durante uma temporada valem para a seguinte.

## E) Limitações honestas desta versão

- O parser externo `demoparser2` não estava instalável no ambiente em que o
  projeto foi criado; a leitura da demo real não foi confirmada por execução.
- A identificação do vencedor ainda precisa ser conferida pelo administrador.
- Sem API direta do SCOPE.GG: a importação é feita por arquivo ou CSV.
- Não extrai HLTV Rating, KAST, trade kills, clutches e boa parte das missões
  avançadas a partir da demo, embora o banco já guarde alguns desses campos.
- Data e placar devem ser revisados antes de salvar; há deduplicação por SHA-256
  para demos e por conteúdo para CSV, mas a **mesma partida** enviada em duas
  fontes diferentes pode gerar duplicidade. Não faça isso.
- O calendário quinzenal e o registro de títulos estão implementados; votação integrada ainda é evolução futura.
- Modo de administrador por senha compartilhada, não contas individuais.
  Defina senha forte e não a compartilhe com o grupo.

## F) Estrutura do repositório

```
apps/
  streamlit/    app Streamlit (app.py, telas, estilos, assets/ e tests/)
  api/          API FastAPI (edb_api/), Dockerfile e testes
  web/          novo frontend Next.js e testes de acessibilidade (Playwright)
packages/
  edb/          regras e dados compartilhados: core, season_rankings, season_system,
                storage, demo_importer, team_draw etc.
db/             supabase_schema.sql e migrations/
docs/           ARQUITETURA, PUBLICAR e REGULAMENTO
scripts/        inspect_demo.py (testar uma demo pelo terminal)
.streamlit/     configuração e secrets do Streamlit (a hospedagem lê daqui)
app.py          entrada de compatibilidade que chama apps/streamlit/app.py
requirements.txt  dependências do app Streamlit (a hospedagem lê daqui)
pytest.ini      configuração dos testes de todo o repositório
```

Regras e cálculos ficam em `packages/edb`; as telas do Streamlit e a API só os importam.
Visão geral do novo frontend e da API: [docs/ARQUITETURA.md](docs/ARQUITETURA.md).

Para verificar as regras: `python -m pytest -q` na raiz (os testes da API pedem
`pip install -r apps/api/requirements-dev.txt`).
