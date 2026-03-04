run_socat_locally () {
    # `socat` should only be installed if we are in a -local container.
    # If it isn't installed, don't run the command.
    if [[ $TARGET_ENV == "local" ]]; then
        if command -v socat &>/dev/null; then
            socat TCP-LISTEN:9090,fork,reuseaddr TCP:host.docker.internal:9090 &
            echo "🔵 running socat"
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

write_bfd_certs_to_tmp () {
    if [[ $TARGET_ENV == "local" ]]; then
        mkdir -p /tmp/bfd/certs
        echo "${BFD_KEY_PEM_B64}" | base64 --decode > /tmp/bfd/certs/key.pem
        echo "${BFD_CERT_PEM_B64}" | base64 --decode > /tmp/bfd/certs/cert.pem
    else
        # Fargate: certs injected as env vars from SM auto-discovery
        # SM /bb2/{env}/app/fhir_key_pem → FHIR_KEY_PEM
        # SM /bb2/{env}/app/fhir_cert_pem → FHIR_CERT_PEM
        mkdir -p /tmp/certstore
        echo "${FHIR_KEY_PEM}" | base64 --decode > /tmp/certstore/ca.key.nocrypt.pem
        echo "${FHIR_CERT_PEM}" | base64 --decode > /tmp/certstore/ca.cert.pem
    fi
    return 0
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
    else
        # Fargate: check /tmp/certstore/
        if [[ -z $(grep '[^[:space:]]' /tmp/certstore/ca.key.nocrypt.pem) ]]; then
            echo "⛔ BFD ca.key.nocrypt.pem is empty"
            return 1
        fi

        if [[ -z $(grep '[^[:space:]]' /tmp/certstore/ca.cert.pem) ]]; then
            echo "⛔ BFD ca.cert.pem is empty"
            return 1
        fi
    fi

    return 0
}

write_tls_certs_to_tmp () {
    if [[ $TARGET_ENV == "local" ]]; then
        mkdir -p /tmp/nginx/certs
        echo "${NGINX_KEY_PEM}" | base64 --decode > /tmp/nginx/certs/key.pem
        echo "${NGINX_CERT_PEM}" | base64 --decode > /tmp/nginx/certs/cert.pem
    else
        # Fargate: certs injected as env vars from SM auto-discovery
        # SM /bb2/{env}/app/www_key_file → WWW_KEY_FILE
        # SM /bb2/{env}/app/www_combined_crt → WWW_COMBINED_CRT
        mkdir -p /tmp/certstore/tls
        echo "${WWW_KEY_FILE}" | base64 --decode > /tmp/certstore/tls/key.pem
        echo "${WWW_COMBINED_CRT}" | base64 --decode > /tmp/certstore/tls/cert.pem
    fi
    return 0
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

launch_blue_button () {
    # Start BBAPI via `gunicorn`
    if [[ $TARGET_ENV == "local" ]]; then
        echo "🟦 local run options"
        gunicorn \
            hhs_oauth_server.wsgi:application \
            --worker-tmp-dir /dev/shm \
            --bind 0.0.0.0:${GUNICORN_PORT} \
            --workers ${GUNICORN_WORKERS} \
            --timeout ${GUNICORN_TIMEOUT} \
            --reload \
            --log-level debug
    else
        # Fargate: gunicorn handles TLS directly with DigiCert certs (no nginx)
        # Matches BFD/AB2D pattern — app server handles TLS, ALB does external termination
        # newrelic-admin run-program auto-configures the NR agent from NEW_RELIC_* env vars
        newrelic-admin run-program \
            gunicorn \
            hhs_oauth_server.wsgi:application \
            --certfile /tmp/certstore/tls/cert.pem \
            --keyfile /tmp/certstore/tls/key.pem \
            --worker-tmp-dir /dev/shm \
            --bind 0.0.0.0:8443 \
            --workers ${GUNICORN_WORKERS} \
            --timeout ${GUNICORN_TIMEOUT} \
            --log-level info
    fi

    return 0
}
