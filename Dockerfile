FROM python:3.9.19-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dépendances système COMPLÈTES pour build Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    libffi-dev \
    libssl-dev \
    python3-dev \
    libopenblas-dev \
    liblapack-dev \
    libstdc++6 \
    supervisor \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip AVANT toute chose
RUN pip install --upgrade pip setuptools wheel

# Dépendances Python
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Code applicatif
COPY . .

# Supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Sécurité
RUN useradd -m appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8050

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
