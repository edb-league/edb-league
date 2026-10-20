# edb

Regras e dados da EDB LEAGUE: ranking Elite, Superação, XP e BAGRES, temporadas e BO3, sorteio de times,
medalhas, leitura de demos e acesso ao banco (SQLite local ou Supabase). É usado pelo app Streamlit
(`apps/streamlit`) e pela API (`apps/api`).

Não importa Streamlit nem FastAPI. Os módulos `fixture_cards` e `match_cards` ainda misturam HTML com dados,
porque a API reaproveita as funções de dados deles.

```python
from edb.core import enrich
from edb.season_rankings import season_boards
```

Sem instalar, adicione `packages/edb` ao `PYTHONPATH`. Para instalar em modo editável: `pip install -e packages/edb`.
Testes: `python -m pytest packages/edb/tests` (a partir da raiz do repositório).
