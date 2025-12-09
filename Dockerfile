# -----------------------------
# Base image
# -----------------------------
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# -----------------------------
# System deps (psycopg2, etc.)
# -----------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Python deps
# -----------------------------
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# -----------------------------
# App code
# -----------------------------
COPY . .

# -----------------------------
# Expose & default command
# -----------------------------

EXPOSE 8000

# Можно менять команду при запуске контейнера,
# но по умолчанию стартует API.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
