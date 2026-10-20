# Construa a partir da raiz do repositório, para incluir os módulos Python de regras:
#   docker build -f api/Dockerfile -t edb-api .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY api/requirements.txt api/requirements.txt
RUN pip install -r api/requirements.txt

# Módulos de regras reaproveitados do app Streamlit (somente leitura pela API).
COPY *.py sample_scoreboard.csv ./
COPY api ./api

RUN useradd --create-home --uid 10001 edb && chown -R edb /app
USER edb

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import os,urllib.request as u; u.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/api/health', timeout=4)"

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
