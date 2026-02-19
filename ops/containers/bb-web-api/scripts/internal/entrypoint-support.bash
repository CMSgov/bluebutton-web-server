launch_blue_button () {
    # Start BBAPI via `gunicorn`
    if [[ $TARGET_ENV == "local" ]]; then
        echo local run options
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


write_nginx_certs_to_tmp () {
    mkdir -p /tmp/ssl/certs
    if [[ $TARGET_ENV == "local" ]]; then
        pushd /tmp
            openssl req -x509 -newkey rsa:4096 \
                -keyout /tmp/ssl/certs/key.pem \
                -out /tmp/ssl/certs/cert.pem \
                -sha256 \
                -days 3650 \
                -nodes \
                -subj "/C=XX/ST=StateName/L=CityName/O=CompanyName/OU=CompanySectionName/CN=CommonNameOrHostname"
        popd
        return 0
    else
        echo "not implemented"
        return 1
    fi
    # Should not get here
    return 2
}