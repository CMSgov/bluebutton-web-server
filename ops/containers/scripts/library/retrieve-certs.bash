#!/usr/bin/env bash

get_certificate () {
    if [[ "$env" == "local" ]]; then
        CERT_PATH="${SCRIPT_DIR}/certs/local-self-signed-cert.crt"
        CERT_STRING=$(<"$CERT_PATH")
    else
        CERT_STRING="GET_CERT_FROM_ENV"
    fi
    # Failure to quote variables can lead to loss of newlines.
    echo "$CERT_STRING"
    return 0
}

get_key() {
    if [[ "$env" == "local" ]]; then
        KEY_STRING=$(<"${SCRIPT_DIR}/certs/local-self-signed-key.key")
    else
        KEY_STRING="GET_KEY_FROM_ENV"
    fi
    # Failure to quote variables can lead to loss of newlines.
    echo "$KEY_STRING"
    return 0
}