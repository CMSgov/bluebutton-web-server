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
    mkdir -p ${DJANGO_FHIR_CERTSTORE}
    if [[ $TARGET_ENV == "local" ]]; then
        echo "${BFD_KEY_PEM_B64}" | base64 --decode > ${DJANGO_FHIR_CERTSTORE}/key.pem
        echo "${BFD_CERT_PEM_B64}" | base64 --decode > /${DJANGO_FHIR_CERTSTORE}/cert.pem
        return 0
    else
        # Fargate: certs injected as env vars from SM auto-discovery
        # SM /bb2/{env}/app/fhir_key_pem → FHIR_KEY_PEM
        # SM /bb2/{env}/app/fhir_cert_pem → FHIR_CERT_PEM
        echo "${FHIR_KEY_PEM}" | base64 --decode > ${DJANGO_FHIR_CERTSTORE}/ca.key.nocrypt.pem
        echo "${FHIR_CERT_PEM}" | base64 --decode > ${DJANGO_FHIR_CERTSTORE}/ca.cert.pem

        return 1
    fi

    # Should not get here
    return 2
}

# write_bfd_certs_to_tmp () {
#     mkdir -p /tmp/certstore
#     if [[ $TARGET_ENV == "local" ]]; then
#         echo "${BFD_KEY_PEM_B64}" | base64 --decode > /tmp/certstore/ca.key.nocrypt.pem
#         echo "${BFD_CERT_PEM_B64}" | base64 --decode > /tmp/certstore/ca.cert.pem
#     else
#         # Fargate: certs injected as env vars from SM auto-discovery
#         # SM /bb2/{env}/app/fhir_key_pem → FHIR_KEY_PEM
#         # SM /bb2/{env}/app/fhir_cert_pem → FHIR_CERT_PEM
#         echo "${FHIR_KEY_PEM}" | base64 --decode > /tmp/certstore/ca.key.nocrypt.pem
#         echo "${FHIR_CERT_PEM}" | base64 --decode > /tmp/certstore/ca.cert.pem
#     fi
#     return 0

check_bfd_certs_are_not_empty () {

    if [[ $TARGET_ENV == "local" ]]; then
        # Make sure the files are not empty
        if [[ -z $(grep '[^[:space:]]' ${DJANGO_FHIR_CERTSTORE}/key.pem) ]]; then
            echo "⛔ BFD key.pem is empty"
            return 1
        fi

        if [[ -z $(grep '[^[:space:]]' ${DJANGO_FHIR_CERTSTORE}/cert.pem) ]]; then
            echo "⛔ BFD cert.pem is empty"
            return 1
        fi
    fi
    
    return 0
}

possibly_migrate_or_collectstatic_if_local () {
    echo "🟦 possibly migrate or collectstatic"

    if [[ $TARGET_ENV == "local" ]]; then
        if [[ "${MIGRATE}" == "1" ]]
        then
            echo "🔵 running migrate"
            python manage.py migrate
            echo "🔵 done running migrate ; bring down the stack"
            exit 0
        fi

        if [[ "${COLLECTSTATIC}" == "1" ]]
        then    
            echo "🔵 running collectstatic"
            python manage.py collectstatic --noinput
            echo "🔵 done running collectstatic; bring down the stack"
            exit 0
        fi
    fi
}

launch_blue_button () {
    # Start BBAPI via `gunicorn`
    if [[ $TARGET_ENV == "local" ]]; then
        # --bind 0.0.0.0:${GUNICORN_PORT} \
        mkdir -p /tmp/gunicorn
        echo "🟦 local run options"
        gunicorn \
            hhs_oauth_server.wsgi:application \
            --worker-tmp-dir /tmp/gunicorn \
            --bind 0.0.0.0:${GUNICORN_PORT} \
            --workers ${GUNICORN_WORKERS} \
            --timeout ${GUNICORN_TIMEOUT} \
            --reload \
            --log-level debug
    else
        gunicorn \
            hhs_oauth_server.wsgi:application \
            --worker-tmp-dir /tmp/gunicorn \
            --bind 0.0.0.0:${GUNICORN_PORT} \
            --workers ${GUNICORN_WORKERS} \
            --timeout ${GUNICORN_TIMEOUT} \
            --reload \
            --log-level debug
    fi

    return 0
}
