
FROM python:3.12-slim

WORKDIR /app

# Install CA certificates and trust the Avast root certificate
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY certs/avast-root.crt /usr/local/share/ca-certificates/avast-root.crt
COPY certs/netfree-root-x2-rsa.crt /usr/local/share/ca-certificates/netfree-root-x2-rsa.crt

RUN update-ca-certificates

RUN echo "===== NETFREE CERTIFICATE CHAIN =====" \
    && openssl s_client -showcerts \
    -connect pypi.org:443 \
    -servername pypi.org \
    </dev/null 2>/dev/null \
    | awk '/BEGIN CERTIFICATE/{n++} n>0{print > ("/tmp/cert" n ".pem")}' \
    && for f in /tmp/cert*.pem; do \
        echo "===== $f ====="; \
        openssl x509 -in "$f" -noout -subject -issuer; \
    done

# Temporary SSL diagnostics
RUN echo "===== CHECK 1: Avast certificate =====" \
    && openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt /usr/local/share/ca-certificates/avast-root.crt \
    && echo "===== CHECK 2: Installed Avast certificate =====" \
    && ls -l /etc/ssl/certs/*avast* \
    && echo "===== CHECK 3: Certificate presented by PyPI =====" \
    && openssl s_client -connect pypi.org:443 -servername pypi.org -CAfile /etc/ssl/certs/ca-certificates.crt </dev/null 2>&1 | grep -E "subject=|issuer=|Verify return code|verify error" || true
# Tell pip to use the system CA certificates
ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt

# Use the same trusted certificates for Python HTTPS clients
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]