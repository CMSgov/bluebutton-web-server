#!/usr/bin/env bash

# This variable determines if we're going to fetch
# cert/salt values from the secret manager.
# We assume yes, but set it to `no` when running fully locally.
export CERT_AND_SALT="YES"

set_fhir_urls () {
    echo "✅ set_fhir_urls"

    if [[ "${ENV}" == "local" ]]; then
        echo "🆗 No FHIR URLs set for local testing."
    #####
    # TEST
    elif [[ "${ENV}" == "test" ]]; then
        export FHIR_URL="${FHIR_URL_TEST}"
        export FHIR_URL_V3="${FHIR_URL_V3_TEST}"

    #####
    # SBX
    elif [[ "${ENV}" == "sbx" ]]; then
        export FHIR_URL="${FHIR_URL_SBX}"
        export FHIR_URL_V3="${FHIR_URL_V3_SBX}"
    fi
}

set_profile () {
    echo "✅ set_profile"

    if [[ "${ENV}" == "local" ]]; then
        export PROFILE="mock-sls"
    #####
    # TEST
    elif [[ "${ENV}" == "test" ]]; then
        export PROFILE="slsx"
    #####
    # SBX
    elif [[ "${ENV}" == "sbx" ]]; then
        export PROFILE="slsx"
    fi
}

retrieve_certs () {
    echo "✅ retrieve_certs"

    if [[ "${ENV}" == "local" ]]; then
        echo "🆗 Running locally. Not retrieving certs."
        echo "🆗 Running locally. Not retrieving salt."
        CERT_AND_SALT="NO"
        export CERT_SUFFIX=""
        export DJANGO_USER_ID_SALT="6E6F747468657265616C706570706572"
        export DJANGO_USER_ID_ITERATIONS="2"
    #####
    # TEST
    elif [[ "${ENV}" == "test" ]]; then
        export CERT_SUFFIX="_test"
        export PROFILE="slsx"
    #####
    # SBX
    elif [[ "${ENV}" == "sbx" ]]; then
        export CERT_SUFFIX=""
        export PROFILE="slsx"
    fi

    if [[ "${CERT_AND_SALT}" == "YES" ]]; then
        # We will (rudely) create a .bb2 directory in the user's homedir.
        # Let's call that BB2_CONFIG_DIR
        export BB2_CONFIG_DIR="${HOME}/.bb2"
        mkdir -p "${BB2_CONFIG_DIR}"
        # And, lets put the certs in their own subdir.
        export BB2_CERTSTORE="${BB2_CONFIG_DIR}/certstore"
        mkdir -p "${BB2_CERTSTORE}"

        CERT="ca.cert.pem"
        KEY="ca.key.nocrypt.pem"

        # Remove them first
        rm -f "${BB2_CERTSTORE}/$CERT"
        rm -f "${BB2_CERTSTORE}/$KEY"

        echo "🎁 Retrieving certs for the '${ENV}' environment with suffix '${CERT_SUFFIX}'."
        aws secretsmanager get-secret-value \
            --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_certificate${CERT_SUFFIX} \
            --query 'SecretString' \
            --output text | base64 -d > "${BB2_CERTSTORE}/ca.cert.pem"

        if [ $? -ne 0 ]; then
            echo "⛔ Failed to retrieve cert. Exiting."
            return -3
        fi

        aws secretsmanager get-secret-value \
            --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_private_key${CERT_SUFFIX} \
            --query 'SecretString' \
            --output text | base64 -d > "${BB2_CERTSTORE}/ca.key.nocrypt.pem"

        if [ $? -ne 0 ]; then 
            echo "⛔ Failed to retrieve private key. Exiting."
            return -4
        fi

        # Check they really came down.
        declare -a cert_files=($CERT $KEY)
        for FILE in "${cert_files[@]}"; 
        do
            if [ -e "${BB2_CERTSTORE}/${FILE}" ]; then
                echo "  🆗 '$FILE' exists."
            else
                echo "  ⛔ '$FILE' does not exist."
                return -5
            fi
        done

        chmod 600 "${BB2_CERTSTORE}/ca.cert.pem"
        chmod 600 "${BB2_CERTSTORE}/ca.key.nocrypt.pem"

        echo "🆗 Retrieved cert and key for '${ENV}'."
    fi
}

set_salt () {
    echo "✅ set_salt"

    if [ "${ENV}" = "local" ]; then
        echo "🆗 Running locally. Not retrieving salt."
        export DJANGO_USER_ID_SALT="6E6F747468657265616C706570706572"
        export DJANGO_USER_ID_ITERATIONS="2"
        DJANGO_MEDICARE_SLSX_REDIRECT_URI="http://localhost:8000/mymedicare/sls-callback"
        DJANGO_MEDICARE_SLSX_LOGIN_URI="http://localhost:8080/sso/authorize?client_id=bb2api"
        DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="http://msls:8080/health"
        DJANGO_SLSX_TOKEN_ENDPOINT="http://msls:8080/sso/session"
        DJANGO_SLSX_SIGNOUT_ENDPOINT="http://msls:8080/sso/signout"
        DJANGO_SLSX_USERINFO_ENDPOINT="http://msls:8080/v1/users"

        DJANGO_SLSX_CLIENT_ID=bb2api
        DJANGO_SLSX_CLIENT_SECRET="xxxxx"

        DJANGO_SLSX_VERIFY_SSL_INTERNAL="False"

        return 0
    elif [ "${ENV}" = "test" ]; then
        echo "🆗 Retrieving salt/client values for '${ENV}'."
    elif [ "${ENV}" = "sbx" ]; then
        echo "🆗 Retrieving salt/client values for '${ENV}'."
    else
        echo "⛔ ENV must be set to 'test' or 'sbx'."
        echo "  ENV is currently set to '${ENV}'."
        echo "  Exiting."
        return -2
    fi

    # These seem to be the same regardless of the env (test or sbx).
    export DJANGO_USER_ID_SALT=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/django_user_id_salt --query 'SecretString' --output text)
    export DJANGO_USER_ID_ITERATIONS=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/django_user_id_iterations --query 'SecretString' --output text)
    export DJANGO_SLSX_CLIENT_ID=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/slsx_client_id --query 'SecretString' --output text)
    export DJANGO_SLSX_CLIENT_SECRET=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/slsx_client_secret --query 'SecretString' --output text)
    export DJANGO_PASSWORD_HASH_ITERATIONS=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/django_password_hash_iterations --query 'SecretString' --output text)
    
    echo "Setting SLSX endpoint/redirects..."
    export DJANGO_MEDICARE_SLSX_REDIRECT_URI="http://localhost:8000/mymedicare/sls-callback"
    export DJANGO_MEDICARE_SLSX_LOGIN_URI="https://test.medicare.gov/sso/authorize?client_id=bb2api"
    export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="https://test.accounts.cms.gov/health"
    export DJANGO_SLSX_TOKEN_ENDPOINT="https://test.medicare.gov/sso/session"
    export DJANGO_SLSX_SIGNOUT_ENDPOINT="https://test.medicare.gov/sso/signout"
    export DJANGO_SLSX_USERINFO_ENDPOINT="https://test.accounts.cms.gov/v1/users"

    # SLSx credentials
    export DJANGO_SLSX_CLIENT_ID=bb2api
    export DJANGO_SLSX_CLIENT_SECRET=${DJANGO_SLSX_CLIENT_SECRET}

    # SSL verify for internal endpoints can't currently use SSL verification (this may change in the future)
    export DJANGO_SLSX_VERIFY_SSL_INTERNAL="False"
    # export DJANGO_SLSX_VERIFY_SSL_EXTERNAL="True"
    
    echo "🆗 Retrieved salt values."
}