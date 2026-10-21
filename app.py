"""Entrada de compatibilidade para a hospedagem do Streamlit.

O aplicativo está em apps/streamlit/app.py. Este arquivo existe para que o deploy que ainda aponta
para "app.py" na raiz continue funcionando. Depois de trocar o "Main file path" do app no Streamlit
Cloud para apps/streamlit/app.py, ele pode ser apagado.
"""
import runpy
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent / "apps" / "streamlit"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
runpy.run_path(str(APP_DIR / "app.py"), run_name="__main__")
