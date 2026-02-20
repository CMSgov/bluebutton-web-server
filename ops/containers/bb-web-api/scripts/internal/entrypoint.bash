#!/bin/bash
set -e 

source ops/containers/bb-web-api/scripts/internal/gonogo.bash
source ops/containers/bb-web-api/scripts/internal/entrypoint-support.bash

echo "TARGET_ENV: $TARGET_ENV"

# ========== ENV VARS ==========
# (Re-)export the variables we need for the rest of the launch.
# Any per-environment choices for vars happens here, too.
# Makes sure the path is correct in the container for everything we 
# might want to run (nginx, gunicorn, etc.)
export NGINX_TMP=/tmp/nginx
export SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export PATH="$PATH:${HOME}/venv/bin/"
export ENV_S3_STORAGE_BUCKET_NAME=${ENV_S3_STORAGE_BUCKET_NAME:-"MAGIC_ENV_S3_STORAGE_BUCKET_NAME"}
export DJANGO_ADMIN_REDIRECTOR=${DJANGO_ADMIN_REDIRECTOR:-"MAGIC_DJANGO_ADMIN_REDIRECTOR"}
export NGINX_PORT=${NGINX_PORT:-8443}
export GUNICORN_PORT=${GUNICORN_PORT:-8000}
export GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
export GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-120}

# ========== SOCAT ==========
# socat is used locally so that Blue Button can talk to the S3 mock.
# We do not want to run it in production. No particular harm comes from running it
# in production, but we don't need to.
run_socat_locally
gonogo "run_socat_locally"

# ========== BFD ==========
# We need certs to talk to BFD. These are grabbed
# outside the container, but need to be written to /tmp
# before we launch.
write_bfd_certs_to_tmp
gonogo "write_bfd_certs_to_tmp"
check_bfd_certs_are_not_empty
gonogo "check_bfd_certs_are_not_empty"

# ========== NGINX ==========
# We should have our certificates in the secrets. This means they will be made available
# to us here, and they can be written out to files at startup. There are both
# the certs for the container (for HTTPS termination) as well as the BFD certs
# (so we can make upstream calls on the behalf of applications).
write_nginx_certs_to_tmp
gonogo "write_nginx_certs_to_tmp"
# Write the config out to /tmp
configure_nginx
gonogo "configure_nginx"
# Run nginx
run_nginx
gonogo "run_nginx"

# Launch our app
launch_blue_button
tree /tmp
gonogo "LAUNCH BLUE BUTTON"
