gonogo () {
    STEP=$1
    result=$?
    if [[ $result == 0 ]]; then
        echo "✅ OK: $STEP"
        return 0
    else
        echo "⛔ BADNESS: $STEP - $result"
        exit -1
    fi
}

########################################
# check_valid_env
# Makes sure we have one of the three valid
# execution environments.
check_valid_env () {
    if [[ "${bfd}" == "local" ]]; then
        : # This is a no-op.
    #####
    # TEST
    elif [[ "${bfd}" == "test" ]]; then
        :
    #####
    # SBX
    elif [[ "${bfd}" == "sbx" ]]; then
        :
    ##### 
    # PROD
    elif [[ "${bfd}" == "prod" ]]; then
        :
    #####
    # ERR
    else
        echo "⛔ 'bfd' must be set to 'local', 'test', 'sbx', or 'prod'."
        echo "⛔ 'bfd' is currently set to '${bfd}'."
        echo "Exiting."
        return 1
    fi 

    return 0
}

########################################
# check_env_preconditions
# Certain minimal things must be true in order to proceed.
check_env_preconditions () {
    
    if [[ "${TARGET_ENV}" == "local" ]]; then
        if [ "${bfd}" != "local" ]; then
            if [ -z ${KION_ACCOUNT_ALIAS} ]; then
                echo "You must run 'kion f <alias>' before 'make run bfd=${bfd}'."
                echo "Exiting."
                return 1
            fi
        fi

        # https://stackoverflow.com/questions/3601515/how-to-check-if-a-variable-is-set-in-bash
        if [ -z ${bfd} ]; then
            echo "'bfd' not set. Cannot retrieve certs."
            echo "'bfd' must be one of 'local', 'test', or 'sbx'."
            echo "For example:"
            echo "  make run-local bfd=test"
            echo "Exiting."
            return 1
        fi
    fi
    return 0
}

load_env_vars () {
    # By definition, this should only be used when TARGET_ENV == "local"
    # We should not be getting variables in this manner when we are running
    # in a production-like environment.
    if [[ "${TARGET_ENV}" == "local" ]]; then
        export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}"
        export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
        export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}"
        export AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN}"
        export BB2_SERVER_STD2FILE=''
        export BB20_ENABLE_REMOTE_DEBUG="${BB20_ENABLE_REMOTE_DEBUG:-true}"
        export BB20_REMOTE_DEBUG_WAIT_ATTACH="${BB20_REMOTE_DEBUG_WAIT_ATTACH:-false}"
        export DATABASES_CUSTOM="${DATABASES_CUSTOM:-postgres://postgres:toor@db:5432/bluebutton}"
        export DJANGO_FHIR_CERTSTORE="${DJANGO_FHIR_CERTSTORE:-/tmp/bfd/certs}"
        export DJANGO_LOG_JSON_FORMAT_PRETTY="${DJANGO_LOG_JSON_FORMAT_PRETTY:-true}"
        export DJANGO_SECRET_KEY=$(openssl rand -hex 32)
        export DJANGO_SECURE_SESSION="${DJANGO_SECURE_SESSION:-false}"
        export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-hhs_oauth_server.settings.dev}"
        export DJANGO_USER_ID_ITERATIONS="${DJANGO_USER_ID_ITERATIONS:-2}"
        export DJANGO_USER_ID_SALT="${DJANGO_USER_ID_SALT:-6E6F747468657265616C706570706572}"
        export FHIR_URL_SBX="${FHIR_URL_SBX:-https://prod-sbx.fhir.bfd.cmscloud.local}"
        export FHIR_URL_TEST="${FHIR_URL_TEST:-https://test.fhir.bfd.cmscloud.local}"
        export FHIR_URL_V3_SBX="${FHIR_URL_V3_SBX:-https://sandbox.fhirv3.bfd.cmscloud.local}"
        export FHIR_URL_V3_TEST="${FHIR_URL_V3_TEST:-https://test.fhirv3.bfd.cmscloud.local}"
        export OAUTHLIB_INSECURE_TRANSPORT="${OAUTHLIB_INSECURE_TRANSPORT:-true}"
        export POSTGRES_DB="${POSTGRES_DB:-bluebutton}"
        export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-toor}"
        export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
        export RUN_ONLINE_TESTS="${RUN_ONLINE_TESTS:-true}"
        export RUNNING_IN_LOCAL_STACK="${RUNNING_IN_LOCAL_STACK:-true}"
        export SUPER_USER_EMAIL="${SUPER_USER_EMAIL:-bluebutton@example.com}"
        export SUPER_USER_NAME="${SUPER_USER_NAME:-root}"
        export SUPER_USER_PASSWORD="${SUPER_USER_PASSWORD:-blue123}"
        return 0
    else
        echo "⛔ cannot load env vars for non-local environments."
        return 1
    fi
}

########################################
# check_env_after_setup
# After setting up the env, we need to make sure that one or two
# variables are now present that would not have been otherwise.
check_env_after_setup () {
    if [ -z ${OAUTHLIB_INSECURE_TRANSPORT} ]; then
        echo "We need insecure transport when running locally."
        echo "OAUTHLIB_INSECURE_TRANSPORT was not set to true."
        echo "Something went badly wrong."
        echo "Exiting."
        return 1
    fi
    return 0
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
        FHIR_URL="${FHIR_URL_TEST}"
        FHIR_URL_V3="${FHIR_URL_V3_TEST}"
        LOCAL_TESTING_TARGET="test"
    #####
    # SBX
    elif [[ "${bfd}" == "sbx" ]]; then
        FHIR_URL="${FHIR_URL_SBX}"
        FHIR_URL_V3="${FHIR_URL_V3_SBX}"
        # FIXME: Do we use "impl" or "sbx"? ...
        LOCAL_TESTING_TARGET="impl"

    elif [[ "${bfd}" == "prod" ]]; then
        echo "⛔ no way to set BFD urls for prod when running locally"
        return 1
    fi

    return 0
}

########################################
# retrieve_bfd_certs
# Download the certs from the secrets store.
# Put them in a "BB2 config directory" in the developer's
# home directory. This keeps them out of the tree.

# This variable determines if we're going to fetch
# cert/salt values from the secret manager.
# We assume yes, but set it to `no` when running fully locally.
export CERT_AND_SALT="YES"

retrieve_bfd_certs () {
    if [[ "${bfd}" == "local" ]]; then
        echo "🆗 Running locally. Not retrieving certs."
        echo "🆗 Running locally. Not retrieving salt."
        unset BFD_CERT_PEM_B64
        unset BFD_KEY_PEM_B64
    elif [[ "${bfd}" == "test" ]]; then
        export CERT_SUFFIX="_test"
        export PROFILE="slsx"
        BFD_CERT_PEM_B64=$(aws secretsmanager get-secret-value \
            --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_certificate_test \
            --query 'SecretString' \
            --output text)
        BFD_KEY_PEM_B64=$(aws secretsmanager get-secret-value \
            --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_private_key_test \
            --query 'SecretString' \
            --output text)
    elif [[ "${bfd}" == "sbx" ]]; then
        BFD_CERT_PEM_B64=$(aws secretsmanager get-secret-value \
            --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_certificate \
            --query 'SecretString' \
            --output text)
        BFD_KEY_PEM_B64=$(aws secretsmanager get-secret-value \
            --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_private_key \
            --query 'SecretString' \
            --output text)
    elif [[ "${bfd}" == "prod" ]]; then
        echo "⛔ fetching certs for prod target not supported locally."
        return 1
    fi

    return 0
}

retrieve_nginx_certs () {
    KEY_TEMP=$(mktemp)
    CERT_TEMP=$(mktemp)
    if [[ $TARGET_ENV == "local" ]]; then
        openssl req -x509 -newkey rsa:4096 \
            -keyout $KEY_TEMP \
            -out $CERT_TEMP \
            -sha256 \
            -days 3650 \
            -nodes \
            -subj "/C=XX/ST=StateName/L=CityName/O=CompanyName/OU=CompanySectionName/CN=CommonNameOrHostname" \
            >/dev/null 2>&1
        NGINX_KEY_PEM_B64=$(<$KEY_TEMP)
        export NGINX_KEY_PEM_B64=$(echo "${NGINX_CERT_PEM_B64}" | base64)
        NGINX_CERT_PEM_B64=$(<$CERT_TEMP)
        export NGINX_CERT_PEM_B64=$(echo "${NGINX_CERT_PEM_B64}" | base64)
    else
        rm -f $KEY_TEMP
        rm -f $CERT_TEMP
        echo "⛔ nginx certs must be fetched in cloud environments."
        return 1
    fi
    
    rm -f $KEY_TEMP
    rm -f $CERT_TEMP
    return 0
}

########################################
# configure_slsx
# How do we want to authenticate? Mock or live?
configure_slsx () {
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
    elif [ "${bfd}" = "sbx" ] || [ "${bfd}" = "prod" ]; then
        echo "🆗 Retrieving salt/client values for '${bfd}'."
    else
        echo "⛔ bfd must be set to 'test', 'sbx', or 'prod'."
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