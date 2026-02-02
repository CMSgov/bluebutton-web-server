#!/bin/bash
set -e

# docker-entrypoint.sh
# Decodes base64-encoded certificates from ECS Secrets Manager injection
# Mirrors user_data.tpl cert decode logic from bluebutton-web-deployment

CERTSTORE="/app/certstore"
SSL_DIR="/etc/ssl/certs"

mkdir -p "$CERTSTORE"

# Decode SSL certificates (matches user_data.tpl lines 43-46)
# Original: aws secretsmanager get-secret-value --secret-id /bb2/${env}/app/www_key_file |base64 -d > /etc/ssl/certs/key.pem
if [ -n "${WWW_KEY_FILE_B64:-}" ]; then
    echo "$WWW_KEY_FILE_B64" | base64 -d > "$SSL_DIR/key.pem"
    chmod 0640 "$SSL_DIR/key.pem"
    echo "[entrypoint] SSL key written to $SSL_DIR/key.pem"
fi

if [ -n "${WWW_COMBINED_CRT_B64:-}" ]; then
    echo "$WWW_COMBINED_CRT_B64" | base64 -d > "$SSL_DIR/cert.pem"
    chmod 0640 "$SSL_DIR/cert.pem"
    echo "[entrypoint] SSL cert written to $SSL_DIR/cert.pem"
fi

# Decode FHIR certificates (matches user_data.tpl lines 48-52)
# Original: /var/pyapps/hhs_o_server/certstore/ca.cert.pem
if [ -n "${FHIR_CERT_PEM_B64:-}" ]; then
    echo "$FHIR_CERT_PEM_B64" | base64 -d > "$CERTSTORE/ca.cert.pem"
    chmod 0640 "$CERTSTORE/ca.cert.pem"
    echo "[entrypoint] FHIR cert written to $CERTSTORE/ca.cert.pem"
fi

if [ -n "${FHIR_KEY_PEM_B64:-}" ]; then
    echo "$FHIR_KEY_PEM_B64" | base64 -d > "$CERTSTORE/ca.key.nocrypt.pem"
    chmod 0640 "$CERTSTORE/ca.key.nocrypt.pem"
    echo "[entrypoint] FHIR key written to $CERTSTORE/ca.key.nocrypt.pem"
fi

# Export Django certstore path
export DJANGO_FHIR_CERTSTORE="$CERTSTORE"

echo "[entrypoint] Certificate setup complete"

# Execute the CMD (Gunicorn)
exec "$@"
