#!/bin/bash

# Here we reach into the environment provided to us and 
# re-export variables for use in the scripts. Any conditional
# work for making sure the right values are set in the right
# environments also happens here.
export_env_vars () {
    export ENV_S3_STORAGE_BUCKET_NAME="MAGIC_ENV_S3_STORAGE_BUCKET_NAME"
    export DJANGO_ADMIN_REDIRECTOR="MAGIC_DJANGO_ADMIN_REDIRECTOR"
    export NGINX_PORT="8443"
    export GUNICORN_PORT="8000"
    export GUNICORN_WORKERS=4
    export GUNICORN_TIMEOUT=120
}