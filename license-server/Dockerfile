# Build do webhook/license server numa imagem pequena.
# Imagem de runtime: python:3.12-slim (leve, sem build deps pesados).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copia apenas o license-server (não a aplicação desktop).
# Primeiro o requirements para aproveitar o cache de layers do build.
COPY license-server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY license-server/*.py /app/

# Cria um volume para a base de dados SQLite persistente.
# O Render monta um disco neste caminho se AIRMOUSE_LS_DB apontar para cá.
RUN mkdir -p /data

EXPOSE 8000

# Uvicorn é instável com -reload em produção; corremos com 1 worker
# porque o SQLite + máquina de licenças é estado local em memória por worker.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
