#!/bin/bash
set -e 

source ops/containers/bb-web-api/scripts/internal/gonogo.bash
source ops/containers/bb-web-api/scripts/internal/entrypoint-support.bash

# `socat` should only be installed if we are in a -local container.
# If it isn't installed, don't run the command.
if command -v socat &>/dev/null; then
    echo "🔵 running socat localhost:9090 -> docker.internal:9090"
    socat TCP-LISTEN:9090,fork,reuseaddr TCP:host.docker.internal:9090 &
fi

NGINX_TMP=/tmp/nginx
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PATH="$PATH:${HOME}/venv/bin/"

# ========== ENV VARS ==========
# (Re-)export the variables we need for the rest of the launch.
# Any per-environment choices for vars happens here, too.
# Makes sure the path is correct in the container for everything we 
# might want to run (nginx, gunicorn, etc.)
export ENV_S3_STORAGE_BUCKET_NAME=${ENV_S3_STORAGE_BUCKET_NAME:-"MAGIC_ENV_S3_STORAGE_BUCKET_NAME"}
export DJANGO_ADMIN_REDIRECTOR=${DJANGO_ADMIN_REDIRECTOR:-"MAGIC_DJANGO_ADMIN_REDIRECTOR"}
export NGINX_PORT=${NGINX_PORT:-8443}
export GUNICORN_PORT=${GUNICORN_PORT:-8000}
export GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
export GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-120}

# ========== CERTIFICATES ==========
# We should have our certificates in the secrets. This means they will be made available
# to us here, and they can be written out to files at startup. There are both
# the certs for the container (for HTTPS termination) as well as the BFD certs
# (so we can make upstream calls on the behalf of applications).
write_nginx_certs_to_tmp
gonogo "WRITE NGINX CERTS TO /tmp"


# ========== NGINX ==========
# Link the params into /tmp so they are adjacent to the config.
mkdir -p ${NGINX_TMP}/tmp
cat ${HOME}/bb/ops/containers/bb-web-api/files/internal/nginx.conf.in | ${BOTONBIN}/envsubst  > ${NGINX_TMP}/nginx.conf
rm -f ${NGINX_TMP}/uwsgi_params
ln -s /etc/nginx/uwsgi_params ${NGINX_TMP}/uwsgi_params
nginx -c ${NGINX_TMP}/nginx.conf &

launch_blue_button
gonogo "LAUNCH BLUE BUTTON"
