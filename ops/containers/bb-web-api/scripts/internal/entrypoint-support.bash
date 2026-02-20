run_socat_locally () {
    # `socat` should only be installed if we are in a -local container.
    # If it isn't installed, don't run the command.
    if [[ $TARGET_ENV == "local" ]]; then
        if command -v socat &>/dev/null; then
            socat TCP-LISTEN:9090,fork,reuseaddr TCP:host.docker.internal:9090 &
            return 0
        else
            echo "⛔ Could not run socat locally. Badness 10000."
            return 1
        fi
    else
        echo "🔵 choosing not to run socat in production."
        return 0
    fi
}

launch_blue_button () {
    # Start BBAPI via `gunicorn`
    if [[ $TARGET_ENV == "local" ]]; then
        echo "🟦 local run options"
    else
        gunicorn \
            hhs_oauth_server.wsgi:application \
            --worker-tmp-dir /dev/shm \
            --bind 0.0.0.0:${GUNICORN_PORT} \
            --workers ${GUNICORN_WORKERS} \
            --timeout ${GUNICORN_TIMEOUT} \
            --reload \
            --log-level debug
    fi

    return 0
}

write_bfd_certs_to_tmp () {
    mkdir -p /tmp/bfd/certs
    echo "BFD_KEY_PEM_B64: ${BFD_KEY_PEM_B64}"

    if [[ $TARGET_ENV == "local" ]]; then
        echo "${BFD_KEY_PEM_B64}" > /tmp/bfd/certs/key.pem
        echo "${BFD_CERT_PEM_B64}" > /tmp/bfd/certs/cert.pem
        return 0
    else
        # In production, we grab the certs from the envirionment.
        echo "⛔ writing certs in prod environments not supported yet"
        return 1
    fi

    # Should not get here
    return 2
}

check_bfd_certs_are_not_empty () {

    if [[ $TARGET_ENV == "local" ]]; then
        # Make sure the files are not empty
        if [[ -z $(grep '[^[:space:]]' /tmp/bfd/certs/key.pem) ]]; then
            echo "⛔ BFD key.pem is empty"
            return 1
        fi

        if [[ -z $(grep '[^[:space:]]' /tmp/bfd/certs/cert.pem) ]]; then
            echo "⛔ BFD cert.pem is empty"
            return 1
        fi
    fi
    
    return 0
}

write_nginx_certs_to_tmp () {
    mkdir -p /tmp/nginx/certs
    if [[ $TARGET_ENV == "local" ]]; then
        echo "${NGINX_KEY_PEM}" > /tmp/nginx/certs/key.pem
        echo "${NGINX_CERT_PEM}" > /tmp/nginx/certs/cert.pem
        return 0
    else
        # In production, we grab the certs from the envirionment.
        echo "not implemented"
        return 1
    fi
    # Should not get here
    return 2
}

configure_nginx () {
    # This happens in all environments, local and production
    mkdir -p ${NGINX_TMP}/tmp
    cat ${HOME}/bb/ops/containers/bb-web-api/files/internal/nginx.conf.in | ${BOTONBIN}/envsubst  > ${NGINX_TMP}/nginx.conf
    rm -f ${NGINX_TMP}/uwsgi_params
    ln -s /etc/nginx/uwsgi_params ${NGINX_TMP}/uwsgi_params
    
}

run_nginx () {
    # This happens in all environments, local and production
    nginx -c ${NGINX_TMP}/nginx.conf &
    return $?
}