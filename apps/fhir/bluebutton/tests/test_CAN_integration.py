import base64
import hashlib
import os
import secrets
import time
import uuid

import jwt
import requests

from apps.constants import CLIENT_CREDENTIALS, TEST_APP_CLIENT_ID
from apps.dot_ext.constants import CLIENT_ASSERTION_TYPE_VALUE

# Start with building the url
# https://verified.clearme.com/integrations/oauth2/auth?response_type=code&client_id=bluebutton-sample&state=teststate&redirect_uri=http://localhost:3001/api/clear/callback&scope=offline%20openid%20offline_access&code_challenge=<insert_generated_code_challenge_here>&code_challenge_method=S256

# Get the generation of the code challenge and the code verifier
# TODO: Mimic login flow somehow for synthetic user to receive a code value

# POST to the clear token endpoint
# curl --location 'https://verified.clearme.com/integrations/oauth2/token' \
# --header 'Content-Type: application/x-www-form-urlencoded' \
# --header 'Cookie: ' \
# --data-urlencode 'client_id=bluebutton-sample' \
# --data-urlencode 'client_secret=<secret-from-aws>' \
# --data-urlencode 'scope=offline openid offline_access' \
# --data-urlencode 'grant_type=authorization_code' \
# --data-urlencode 'redirect_uri=http://localhost:3001/api/clear/callback' \
# --data-urlencode 'code=<code-from-url>' \
# --data-urlencode 'code_verifier=<generated-code-verifier>'


# Get the client secret from AWS SSM as a environment variable

# TODO: Construct the payload for algorithm and token type
# {
#   "alg": "RS384",
#   "kid": "my-key-id-1",
#   "typ": "JWT"
# }

# TODO: Get a private key to encode the jwt, possibly store this within SOPS/SSM and read it in as an environment variable
# For now, let's just pretend we have the variables read in already

# The output of after we send in the a POST request to BBAPI's token endpoint as the client_assertion

# Use the client_assertion and other params to hit the token endpoint and get back access_token and refresh_token

# Use the generate pkce data function from apps/testclient/utils.py to generate the code challenge and code verifier

# TODO: Construct this (scaffolding below)
# {
#   "iss": "<paste_client_id_here>",
#   "sub": "<paste_client_id_here>",
#   "aud": "https://<paste_env_here>.bluebutton.cms.gov/v3/o/token",
#   "jti": "<paste_jti_here>",
#   "exp": <paste_exp_here>,
#   "extensions": {
#     "cms_smart": {
#       "version": "1",
#       "purpose_of_use": "PATRQT",
#       "id_token": "<paste_id_token_here>"
#     }
#   }
# }

# Ensure the iss and sub are the client id
# jti is a randomly generated uuid
# exp must be within 5 minutes of the current timestamp from unix epoch time


def get_clear_id_token(client_secret: str, code: str, code_verifier: str) -> str:
    """
    Exchanges the authorization code for an ID token from Clear.

    Args:
        client_secret (str): The client secret for the Clear integration.
        code (str): The authorization code received from Clear.
        code_verifier (str): The code verifier used in the PKCE flow.

    Returns:
        str: The ID token received from Clear.
    """
    url = 'https://verified.clearme.com/integrations/oauth2/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'client_id': 'bluebutton-sample',
        'client_secret': client_secret,
        'scope': 'offline openid offline_access',
        'grant_type': 'authorization_code',
        'redirect_uri': 'http://localhost:3001/api/clear/callback',
        'code': code,
        'code_verifier': code_verifier,
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json().get('id_token')


def construct_ial_payload(id_token: str) -> dict:
    """
    Constructs the payload for the IAL (Identity Assurance Level) request to the Blue Button API token endpoint.

    Args:
        id_token (str): The ID token received from Clear.

    Returns:
        dict: A dictionary representing the payload for the IAL request.
    """
    return {
        'iss': TEST_APP_CLIENT_ID,
        'sub': TEST_APP_CLIENT_ID,
        'aud': 'https://localhost:8000/bluebutton.cms.gov/v3/o/token',
        'jti': str(uuid.uuid4()),
        'exp': int(time.time()) + 300,  # Current time + 5 minutes (300 seconds)
        'extensions': {'cms_smart': {'version': '1', 'purpose_of_use': 'PATRQT', 'id_token': id_token}},
    }


def get_access_token_response(client_assertion: str, client_assertion_type: str, grant_type: str, scope: str) -> dict:
    """
    Exchanges the client assertion for an access token from the Blue Button API.

    Args:
        client_assertion (str): The client assertion JWT.
        client_assertion_type (str): The type of client assertion.
        grant_type (str): The grant type for the token request.
        scope (str): The scope for the token request.

    Returns:
        dict: A dictionary containing the access token and other related information.
    """
    url = 'https://localhost:8000/bluebutton.cms.gov/v3/o/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'client_assertion': client_assertion,
        'client_assertion_type': client_assertion_type,
        'grant_type': grant_type,
        'scope': scope,
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()


def generate_pkce_data() -> tuple:
    """
    Generates a code verifier and code challenge for the PKCE flow.

    Returns:
        tuple: A tuple containing the code verifier and code challenge.
    """
    # Generate a random code verifier
    code_verifier = secrets.token_urlsafe(64)

    # Generate the code challenge using SHA256 and base64url encoding
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).decode('utf-8')

    return code_verifier, code_challenge


# What it would look like all together in a test function
def test_clear_integration_flow():
    """
    Test the Clear integration flow by simulating the steps to obtain an access token from the Blue Button API.
    """
    code_verifier, code_challenge = generate_pkce_data()
    # Start with building the url
    # clear_login_url = f'https://verified.clearme.com/integrations/oauth2/auth?response_type=code&client_id=bluebutton-sample&state=teststate&redirect_uri=http://localhost:3001/api/clear/callback&scope=offline%20openid%20offline_access&code_challenge={code_challenge}&code_challenge_method=S256'
    # TODO: Somehow need to get the code from the Clear login url, possibly by mimicking a user login or using a test account
    # Code challenge will need to be used here in the URL to get the code from Clear, and then the code will be used to get the id_token from Clear
    authorization_code = 'replace_me_with_actual_authorization_code'

    # TODO: Replace with actual env var name
    client_secret = os.getenv('CLEAR_CLIENT_SECRET', 'your_client_secret_here')
    id_token = get_clear_id_token(client_secret, authorization_code, code_verifier)

    ial_payload = construct_ial_payload(id_token)

    # Get the private key from AWS SSM as an environment variable
    # TODO: Replace with actual env var name
    private_key = os.getenv('PRIVATE_KEY', 'your_private_key_here')
    client_assertion = jwt.encode(ial_payload, private_key, algorithm='RS384')

    # Make the call to the token endpoint with the client_assertion and other params to get back access_token and refresh_token
    client_assertion_type = CLIENT_ASSERTION_TYPE_VALUE
    grant_type = CLIENT_CREDENTIALS
    scope = 'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs'

    access_token_response = get_access_token_response(client_assertion, client_assertion_type, grant_type, scope)

    assert 'access_token' in access_token_response, 'Access token not found in response'
