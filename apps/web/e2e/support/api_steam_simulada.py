"""API só para os testes de navegador: igual à real, mas sem perguntar nada à Steam de verdade.

Os testes de e2e fingem ser a Steam (interceptam o redirecionamento no navegador) e devolvem uma resposta
assinada à força; aqui a API aceita essa assinatura. Todo o resto da verificação (estado, endereço de retorno,
nonce, identidade) continua valendo. Este arquivo existe só para o Playwright e nunca vai para a produção.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "apps" / "api"))

from edb_api import steam_openid  # noqa: E402
from edb_api.main import create_app  # noqa: E402

steam_openid.check_with_steam = lambda params, timeout=6.0: True
app = create_app()
