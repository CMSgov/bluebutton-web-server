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
    set -o pipefail
    echo "🟦 Writing Certs to ${DJANGO_FHIR_CERTSTORE}"
    mkdir -p "${DJANGO_FHIR_CERTSTORE}"
    echo "${BFD_KEY_PEM_B64}" | base64 --decode > "${DJANGO_FHIR_CERTSTORE}/ca.key.nocrypt.pem" || return 1
    echo "${BFD_CERT_PEM_B64}" | base64 --decode > "${DJANGO_FHIR_CERTSTORE}/ca.cert.pem" || return 1
    set +o pipefail
    return 0
}


check_bfd_certs_are_not_empty () {
    echo "🟦 Check BFD certs are at ${DJANGO_FHIR_CERTSTORE}"
    # Make sure the files are not empty
    if [[ -z $(grep '[^[:space:]]' "${DJANGO_FHIR_CERTSTORE}/ca.key.nocrypt.pem") ]]; then
        echo "⛔ BFD ca.key.nocrypt.pem is empty"
        return 1
    fi

    if [[ -z $(grep '[^[:space:]]' "${DJANGO_FHIR_CERTSTORE}/ca.cert.pem") ]]; then
        echo "⛔ BFD cert.pem is empty"
        return 1
    fi
    echo "🔵 BFD certs are in place"
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

        # TODO - collectstatic does not tear down the stack currently
        if [[ "${COLLECTSTATIC}" == "1" ]]
        then    
            echo "🔵 running collectstatic"
            python manage.py collectstatic --noinput
            echo "🔵 done running collectstatic; bring down the stack"
            exit 0
        fi
    fi
}

write_tls_certs_to_tmp () {
    # Fargate: certs injected as env vars from SM auto-discovery
    # SM /bb2/{env}/app/www_key_file → WWW_KEY_FILE
    # SM /bb2/{env}/app/www_combined_crt → WWW_COMBINED_CRT
    set -o pipefail
    mkdir -p /tmp/certstore/tls
    echo "${WWW_KEY_FILE}" | base64 --decode > /tmp/certstore/tls/key.pem || return 1
    echo "${WWW_COMBINED_CRT}" | base64 --decode > /tmp/certstore/tls/cert.pem || return 1
    set +o pipefail
    return 0
}

check_tls_certs_are_not_empty () {
    echo "🟦 Check TLS certs are at /tmp/certstore/tls"
    if [[ -z $(grep '[^[:space:]]' "/tmp/certstore/tls/key.pem") ]]; then
        echo "⛔ TLS key.pem is empty"
        return 1
    fi

    if [[ -z $(grep '[^[:space:]]' "/tmp/certstore/tls/cert.pem") ]]; then
        echo "⛔ TLS cert.pem is empty"
        return 1
    fi
    echo "🔵 TLS certs are in place"
    return 0
}

launch_blue_button () {
    echo "🟦 Launch Blue Button"
    mkdir -p /tmp/gunicorn
    # Start BBAPI via `gunicorn`
    if [[ $TARGET_ENV == "local" ]]; then
        # --bind 0.0.0.0:${GUNICORN_PORT} \
        echo "🔵 local run options"
        gunicorn \
            hhs_oauth_server.wsgi:application \
            --worker-tmp-dir /tmp/gunicorn \
            --bind 0.0.0.0:${GUNICORN_PORT} \
            --workers ${GUNICORN_WORKERS} \
            --timeout ${GUNICORN_TIMEOUT} \
            --reload \
            --log-level debug
        RESULT=$?
    else
        # Fargate: gunicorn handles TLS directly with DigiCert certs (no nginx)
        # Matches BFD/AB2D pattern — app server handles TLS, ALB does external termination
        # newrelic-admin run-program auto-configures the NR agent from NEW_RELIC_* env vars
        echo "🔵 aws run options"
        newrelic-admin run-program \
            gunicorn \
            hhs_oauth_server.wsgi:application \
            --config /home/boton/bb/gunicorn.conf.py \
            --certfile /tmp/certstore/tls/cert.pem \
            --keyfile /tmp/certstore/tls/key.pem \
            --worker-tmp-dir /tmp/gunicorn \
            --bind 0.0.0.0:8443 \
            --workers ${GUNICORN_WORKERS} \
            --timeout ${GUNICORN_TIMEOUT} \
            --log-level info
    fi

    return $RESULT
}

setup_database_and_users_if_local () {
    echo "🟦 Setup database and users if local"

    if [[ $TARGET_ENV == "local" ]]; then

        # Only create the root user if it doesn't exist.
        result=$(python manage.py shell --verbosity 0 -c "from django.contrib.auth.models import User; print(1) if User.objects.filter(username='${SUPER_USER_NAME}').exists() else print(0)")
        if [[ "$result" == "0" ]]; then
            echo "from django.contrib.auth.models import User; User.objects.create_superuser('${SUPER_USER_NAME}', '${SUPER_USER_EMAIL}', '${SUPER_USER_PASSWORD}')" | python manage.py shell
            echo "🆗 created ${SUPER_USER_NAME} user."
        else
            echo "🆗 ${SUPER_USER_NAME} already exists."
        fi

        python manage.py create_test_feature_switches
        echo "🆗 create_test_feature_switches"

        python manage.py create_admin_groups
        echo "🆗 create_admin_groups"

        python manage.py create_blue_button_scopes
        echo "🆗 create_blue_button_scopes"

        python manage.py create_test_user_and_application

        echo "🆗 create_test_user_and_application"

        python manage.py create_user_identification_label_selection
        echo "🆗 create_user_identification_label_selection"
    fi
}
