# Stage 1: Build dependencies with local SSL certificates
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY certs/avast-root.crt /usr/local/share/ca-certificates/avast-root.crt
COPY certs/netfree-root-x2-rsa.crt /usr/local/share/ca-certificates/netfree-root-x2-rsa.crt

RUN update-ca-certificates

ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Clean production image
FROM python:3.12-slim AS production

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=builder /usr/local /usr/local
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
