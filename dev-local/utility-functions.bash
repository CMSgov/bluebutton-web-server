#!/usr/bin/env bash

########################################
# check_valid_env
# Makes sure we have one of the three valid
# execution environments.
check_valid_env () {
    if [[ "${bfd}" == "local" ]]; then
        # This is a no-op.
        :
    #####
    # TEST
    elif [[ "${bfd}" == "test" ]]; then
        :
    #####
    # SBX
    elif [[ "${bfd}" == "sbx" ]]; then
        :
    #####
    # ERR
    else
        echo "⛔ 'bfd' must be set to 'local', 'test', or 'sbx'."
        echo "⛔ 'bfd' is currently set to '${bfd}'."
        echo "Exiting."
        return -2
    fi 

    echo "✅ check_valid_env"
}

########################################
# clear_canary_variables
# We want one or two variables that we know will be obtained
# via sourcing the .env. Unset them first.
clear_canary_variables () {
    unset OATHLIB_INSECURE_TRANSPORT
    unset DB_MIGRATIONS
}

########################################
# check_env_preconditions
# Certain minimal things must be true in order to proceed.
check_env_preconditions () {
    if [ "${bfd}" != "local" ]; then
        if [ -z ${KION_ACCOUNT_ALIAS} ]; then
            echo "You must run 'kion f <alias>' before 'make run bfd=${bfd}'."
            echo "Exiting."
            return -1
        fi
    fi

    # https://stackoverflow.com/questions/3601515/how-to-check-if-a-variable-is-set-in-bash
    if [ -z ${bfd} ]; then
        echo "'bfd' not set. Cannot retrieve certs."
        echo "'bfd' must be one of 'local', 'test', or 'sbx'."
        echo "For example:"
        echo "  make run-local bfd=test"
        echo "Exiting."
        return -1
    fi

    echo "✅ check_env_preconditions"

}

########################################
# check_env_after_source
# After sourcing in the .env, we need to make sure that one or two
# variables are now present that would not have been otherwise.
check_env_after_source () {

    if [ -z ${OAUTHLIB_INSECURE_TRANSPORT} ]; then
        echo "We need insecure transport when running locally."
        echo "OAUTHLIB_INSECURE_TRANSPORT was not set to true."
        echo "Something went badly wrong."
        echo "Exiting."
        return -1
    fi

    if [ -z ${DB_MIGRATIONS} ]; then
        echo "There should be a DB_MIGRATIONS flag."
        echo "Something went badly wrong."
        echo "Exiting."
        return -1
    fi

    echo "✅ check_env_after_source"
}

########################################
# set_bfd_urls
# Make sure we have the right BFD URLs for testing against.
set_bfd_urls () {
    #####
    # LOCAL
    if [[ "${bfd}" == "local" ]]; then
        echo "⚠️  No FHIR URLs set for local testing."
        echo "   There are no mock BFD endpoints for local testing at this time."
        export LOCAL_TESTING_TARGET="local"
    #####
    # TEST
    elif [[ "${bfd}" == "test" ]]; then
        export FHIR_URL="${FHIR_URL_TEST}"
        export FHIR_URL_V3="${FHIR_URL_V3_TEST}"
        export LOCAL_TESTING_TARGET="test"
    #####
    # SBX
    elif [[ "${bfd}" == "sbx" ]]; then
        export FHIR_URL="${FHIR_URL_SBX}"
        export FHIR_URL_V3="${FHIR_URL_V3_SBX}"
        # FIXME: Do we use "impl" or "sbx"? ...
        export LOCAL_TESTING_TARGET="impl"
    fi

    echo "✅ set_bfd_urls"
}

########################################
# set_auth_profile
# This sets the variables that determine if we will 
# auth locally (mock) or against a live server.
set_auth_profile () {
    if [[ "${bfd}" == "local" ]]; then
        export PROFILE="mock-sls"
    #####
    # TEST
    elif [[ "${bfd}" == "test" ]]; then
        export PROFILE="slsx"
    #####
    # SBX
    elif [[ "${bfd}" == "sbx" ]]; then
        export PROFILE="slsx"
    fi

    echo "✅ set_profile"
}

########################################
# retrieve_certs
# Download the certs from the secrets store.
# Put them in a "BB2 config directory" in the developer's
# home directory. This keeps them out of the tree.

# This variable determines if we're going to fetch
# cert/salt values from the secret manager.
# We assume yes, but set it to `no` when running fully locally.
export CERT_AND_SALT="YES"

retrieve_certs () {

    unset CERT_SUFFIX

    if [[ "${bfd}" == "local" ]]; then
        echo "🆗 Running locally. Not retrieving certs."
        echo "🆗 Running locally. Not retrieving salt."
        CERT_AND_SALT="NO"
        export CERT_SUFFIX=""
    #####
    # TEST
    elif [[ "${bfd}" == "test" ]]; then
        export CERT_SUFFIX="_test"
        export PROFILE="slsx"
    #####
    # SBX
    elif [[ "${bfd}" == "sbx" ]]; then
        export CERT_SUFFIX=""
        export PROFILE="slsx"
    fi


    if [[ "${CERT_AND_SALT}" == "YES" ]]; then
        echo "🎁 Retrieving certs for the '${bfd}' environment with suffix '${CERT_SUFFIX}'."
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
        echo "  Removing ${BB2_CERTSTORE}/$CERT"
        rm -f "${BB2_CERTSTORE}/$CERT"
        echo "  Removing ${BB2_CERTSTORE}/$KEY"
        rm -f "${BB2_CERTSTORE}/$KEY"

        echo "  Fetching ${BB2_CERTSTORE}/$CERT"
        aws secretsmanager get-secret-value \
            --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_certificate${CERT_SUFFIX} \
            --query 'SecretString' \
            --output text | base64 -d > "${BB2_CERTSTORE}/ca.cert.pem"
        
        if [ $? -ne 0 ]; then
            echo "⛔ Failed to retrieve cert. Exiting."
            return -3
        fi

        echo "  Fetching ${BB2_CERTSTORE}/$KEY"
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
            if [ -s "${BB2_CERTSTORE}/${FILE}" ]; then
                echo "  🆗 '$FILE' exists."
            else
                echo "  ⛔ '$FILE' does not exist."
                echo "  ⛔ Try exiting your 'kion' shell and re-authenticating."
                return -5
            fi
        done

        chmod 600 "${BB2_CERTSTORE}/ca.cert.pem"
        chmod 600 "${BB2_CERTSTORE}/ca.key.nocrypt.pem"

    fi

    echo "✅ retrieve_certs"
}

########################################
# set_salt
# The other half of retrieve_certs. Sets up additional
# variables for secure communication with auth servers 
# (or helps set up the mock).
set_salt () {
    if [ "${auth}" = "mock" ]; then
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
        DJANGO_PASSWORD_HASH_ITERATIONS="200000"

        DJANGO_SLSX_VERIFY_SSL_INTERNAL="False"

        return 0
    elif [ "${bfd}" = "test" ]; then
        echo "🆗 Retrieving salt/client values for '${bfd}'."
    elif [ "${bfd}" = "sbx" ]; then
        echo "🆗 Retrieving salt/client values for '${bfd}'."
    else
        echo "⛔ bfd must be set to 'test' or 'sbx'."
        echo "  bfd is currently set to '${bfd}'."
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
    export DJANGO_SLSX_CLIENT_ID="bb2api"
    export DJANGO_SLSX_CLIENT_SECRET="${DJANGO_SLSX_CLIENT_SECRET}"

    # SSL verify for internal endpoints can't currently use SSL verification (this may change in the future)
    export DJANGO_SLSX_VERIFY_SSL_INTERNAL="False"
    export DJANGO_SLSX_VERIFY_SSL_EXTERNAL="True"
    
    echo "✅ set_salt"
}

########################################
# cleanup_docker_stack
# We can't run the stack twice. (Or, it isn't configured to run twice
# with this tooling *yet*.) This walks the open images and closes anything
# that looks like ours. It doesn't *really* know, so if you are doing other work,
# this will probably close things. In short: if you have a `postgres` container, this
# function will try and stop ALL docker containers.
cleanup_docker_stack () {
    DOCKER_PS=$(docker ps -q)

    TAKE_IT_DOWN="NO"
    for id in $DOCKER_PS; do
        NAME=$(docker inspect --format '{{.Config.Image}}' $id)
        if [[ "${NAME}" =~ "postgres" ]]; then
            echo "🤔 I think things are still running. Bringing the stack down."
            TAKE_IT_DOWN="YES"
        fi
    done

    if [ "${TAKE_IT_DOWN}" = "YES" ]; then
        for id in $DOCKER_PS; do
            echo "🛑 Stopping container $id"
            docker stop $id
        done
    fi
}

########################################
# Echo function that includes script name on each line for console log readability
echo_msg () {
		echo "$(basename $0): $*"
}