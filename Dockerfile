FROM python:3.9.19-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dépendances système nécessaires pour pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    python3-dev \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
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
