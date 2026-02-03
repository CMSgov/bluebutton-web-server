#!/usr/bin/env bash



unset CERT_SUFFIX

if [[ "${env}" == "test" ]]; then
    echo "🆗 Running locally. Not retrieving certs."
    echo "🆗 Running locally. Not retrieving salt."
    CERT_AND_SALT="NO"
    export CERT_SUFFIX=""
elif [[ "${env}" == "prod" ]]; then
    export CERT_SUFFIX="_test"
    export PROFILE="slsx"
fi


echo "🎁 Retrieving certs for the '${bfd}' environment with suffix '${CERT_SUFFIX}'."


mkdir -p "${BB2_CERTSTORE}"

CERT="ca.cert.pem"
KEY="ca.key.nocrypt.pem"

# Remove them first
if [ -z "${CA_CERT}" ] && [ -z "${CA_KEY}" ]; then
    export BB2_CONFIG_DIR="${HOME}/.bb2"
    export BB2_CERTSTORE="${BB2_CONFIG_DIR}/certstore"
    echo "  Removing ${BB2_CERTSTORE}/$CERT"
    rm -f "${BB2_CERTSTORE}/$CERT"
    echo "  Removing ${BB2_CERTSTORE}/$KEY"
    rm -f "${BB2_CERTSTORE}/$KEY"

    if [[ ${bfd} == "prod" ]]; then
        echo "  Fetching ${BB2_CERTSTORE}/$CERT"
        aws secretsmanager get-secret-value \
            --secret-id /bb2/prod/app/fhir_cert_pem \
            --query 'SecretString' \
            --output text | base64 -d > "${BB2_CERTSTORE}/ca.cert.pem"
        
        if [ $? -ne 0 ]; then
            echo "⛔ Failed to retrieve cert. Exiting."
            return -3
        fi

        echo "  Fetching ${BB2_CERTSTORE}/$KEY"
        aws secretsmanager get-secret-value \
            --secret-id /bb2/prod/app/fhir_key_pem \
            --query 'SecretString' \
            --output text | base64 -d > "${BB2_CERTSTORE}/ca.key.nocrypt.pem"

        if [ $? -ne 0 ]; then 
            echo "⛔ Failed to retrieve private key. Exiting."
            return -4
        fi
    else
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
    fi

else
    echo "  ℹ️  Act Pipeline. Skipping certificate retrieval."
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


echo "✅ retrieve_certs"
