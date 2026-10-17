# XINXAS LEAGUE — versão inicial (MVP)

Painel web para a liga informal de Counter-Strike 2. Possui perfis com estrelas,
rankings **Elite / Superação / Resenha**, missões, XP, histórico, premiações por
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
streamlit run app.py
```

Caso o PowerShell não permita ativar ambientes virtuais, use diretamente
`.venv\Scripts\python.exe -m pip install -r requirements.txt` e
`.venv\Scripts\python.exe -m streamlit run app.py`.

### macOS / Linux

```bash
cd xinxas-league
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
# Edite .streamlit/secrets.toml e substitua a senha de exemplo.
streamlit run app.py
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
python inspect_demo.py "sua_partida.dem.gz"
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
2. Em **SQL Editor**, execute o conteúdo de `supabase_schema.sql`. O SQL ativa
   Row Level Security e não cria políticas de acesso anônimo.
3. Localize a URL do projeto e a **chave `service_role`** (somente servidor).
   Não use a chave `anon`, e **nunca** publique a chave `service_role`.
4. Crie no [GitHub](https://github.com) um repositório, por exemplo,
   `xinxas-league`, e envie os arquivos desta pasta, **sem**
   `.streamlit/secrets.toml`, demos, senhas ou banco `.db`.
5. Acesse [Streamlit Community Cloud](https://share.streamlit.io), escolha
   **Create app**, selecione o repositório e o arquivo `app.py`.
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

## D) Regras atuais (calibração provisória)

- **Estrelas 1–5**: cadastro manual; podem ser ajustadas em Administração.
- **Elite:** índice = `100 × (0,60 × KPR/0,75 + 0,40 × ADR/75)`;
  se não houver dano, usa `100 × KPR/0,75` (atenção à comparação entre fontes).
- **Superação:** `% de KPR acima da referência por estrelas`;
  referências: 1★ 0,42; 2★ 0,57; 3★ 0,72; 4★ 0,87; 5★ 1,02.
- **Evolução real:** últimas duas partidas vs. duas anteriores; precisa de 4 jogos.
- **Resenha / XP:** 40 XP por partida, 20 XP por vitória informada, 100 XP
  por missão completada de KPR (mín. 8 rounds; no máximo 1 por semana).
- **Teto:** apenas quatro jogos por semana/jogador contam para ranking e XP,
  mas todos ficam registrados para histórico e evolução.
- **MVP e Superação:** exigem no mínimo duas partidas no período. Premiações
  humorísticas e clipes exigem votação manual.

São números de **partida piloto**, não uma verdade sobre o nível dos jogadores.
Vamos recalibrar com 2–3 semanas de dados reais.

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
- Há apenas uma temporada lógica no MVP; gestão de temporadas históricas e
  votação integrada são evoluções futuras.
- Modo de administrador por senha compartilhada, não contas individuais.
  Defina senha forte e não a compartilhe com o grupo.

## F) Arquivos principais

- `app.py`: interface Streamlit.
- `demo_importer.py`: decompressão e leitura dos eventos.
- `core.py`: rankings, missões, XP e evolução.
- `storage.py`: SQLite local / Supabase REST.
- `supabase_schema.sql`: criação do banco online.
- `sample_scoreboard.csv`: transcrição da partida mostrada por print.
- `inspect_demo.py`: teste da demo pelo terminal.
- `tests/`: testes automatizados.

Para verificar as regras: `python -m pytest -q` (se `pytest` estiver instalado).