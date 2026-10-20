# Construa a partir da raiz do repositório, para incluir o pacote compartilhado de regras (packages/edb):
#   docker build -f apps/api/Dockerfile -t edb-api .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY apps/api/requirements.txt apps/api/requirements.txt
RUN pip install -r apps/api/requirements.txt

# Pacote compartilhado de regras (edb) e o código da API.
COPY packages/edb packages/edb
COPY apps/api apps/api

RUN useradd --create-home --uid 10001 edb && chown -R edb /app
USER edb

ENV PORT=8000 \
    PYTHONPATH=/app/packages/edb:/app/apps/api
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import os,urllib.request as u; u.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/api/health', timeout=4)"

CMD ["sh", "-c", "uvicorn edb_api.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
