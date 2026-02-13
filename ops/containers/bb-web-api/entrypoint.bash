#!/bin/bash
set -e 

NGINX_TMP=/tmp/nginx
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PATH="$PATH:${HOME}/venv/bin/"

source ${SCRIPT_DIR}/library/export-env-vars.bash
source ${SCRIPT_DIR}/library/retrieve-certs.bash

# ========== ENV VARS ==========
# (Re-)export the variables we need for the rest of the launch.
# Any per-environment choices for vars happens here, too.
# Makes sure the path is correct in the container for everything we 
# might want to run (nginx, gunicorn, etc.)
export_env_vars

# ========== CERTIFICATES ==========
# We should have our certificates in the secrets. This means they will be made available
# to us here, and they can be written out to files at startup. There are both
# the certs for the container (for HTTPS termination) as well as the BFD certs
# (so we can make upstream calls on the behalf of applications).
mkdir -p /tmp/ssl/certs
CERT=$(get_certificate) 
echo "$CERT" > /tmp/ssl/certs/cert.pem
KEY=$(get_key) 
echo "$KEY" > /tmp/ssl/certs/key.pem

# ========== NGINX ==========
# Link the params into /tmp so they are adjacent to the config.

mkdir -p ${NGINX_TMP}/tmp
cat ${HOME}/bb/ops/containers/bb-web-api/nginx.conf.in | ${PIPBIN}/envsubst  > ${NGINX_TMP}/nginx.conf
ln -s /etc/nginx/uwsgi_params ${NGINX_TMP}/uwsgi_params
nginx -c ${NGINX_TMP}/nginx.conf &

# Start BBAPI via `gunicorn`
gunicorn \
    hhs_oauth_server.wsgi:application \
    --worker-tmp-dir /dev/shm \
    --bind 0.0.0.0:${GUNICORN_PORT} \
    --workers ${GUNICORN_WORKERS} \
    --timeout ${GUNICORN_TIMEOUT} \
    --reload \
    --log-level debug

