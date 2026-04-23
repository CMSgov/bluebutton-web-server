#!/bin/bash

source ops/containers/bb-api/scripts/internal/gonogo.bash
source ops/containers/bb-api/scripts/internal/entrypoint-support.bash

echo "TARGET_ENV: $TARGET_ENV"

# ========== ENV VARS ==========
# (Re-)export the variables we need for the rest of the launch.
# Any per-environment choices for vars happens here, too.
export PATH="$PATH:${HOME}/venv/bin/"
export GUNICORN_PORT=${GUNICORN_PORT:-8000}
export GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
export GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-120}

# ========== DATABASE ==========
# Construct DATABASES_CUSTOM from individual SM secrets (supports credential rotation)
# Django uses dj_database_url to parse this connection string
if [[ $TARGET_ENV == "local" ]]; then
    echo "🔵 using DATABASES_CUSTOM from local environment"
else
    if [[ -n "$DB_USER_NAME" ]]; then
        export DATABASES_CUSTOM="postgres://${DB_USER_NAME}:${DB_USER_PW}@${DB_HOST}:15432/${DB_NAME}?sslmode=require&options=-c role=${DB_ROLE}"
        echo "🔵 DATABASES_CUSTOM constructed from individual DB env vars"
    else
        echo "⛔ DB_USER_NAME not set — DATABASES_CUSTOM not constructed"
    fi
fi

# ========== SOCAT ==========
# socat is used locally so that Blue Button can talk to the S3 mock.
# We do not want to run it in production. No particular harm comes from running it
# in production, but we don't need to.
run_socat_locally
gonogo "run_socat_locally"

# ========== MIGRATE ==========
# When running locally, we may want to run
# python manage.py migrate
#
# or
#
# python manage.py collectstatic
#
# This conditionally does that only if TARGET_ENV=local and
# either MIGRATE=1 or COLLECTSTATIC=1
#
# Must come after socat, so we can talk to the s3mock.
possibly_migrate_or_collectstatic_if_local

# ========== BFD ==========
# We need certs to talk to BFD. These are grabbed
# outside the container, but need to be written to /tmp
# before we launch.
write_bfd_certs_to_tmp
gonogo "write_bfd_certs_to_tmp"
check_bfd_certs_are_not_empty
gonogo "check_bfd_certs_are_not_empty"

# ========== TLS CERTS ==========
# DigiCert certs for HTTPS termination — gunicorn (Fargate)
if [[ $TARGET_ENV != "local" ]]; then
    write_tls_certs_to_tmp
    gonogo "write_tls_certs_to_tmp"
    check_tls_certs_are_not_empty
    gonogo "check_tls_certs_are_not_empty"
fi

# Launch our app
launch_blue_button
gonogo "LAUNCH BLUE BUTTON"
