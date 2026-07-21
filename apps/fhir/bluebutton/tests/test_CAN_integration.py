import base64
import hashlib
import os
import secrets
import time
import urllib
import uuid

import jwt
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

from apps.constants import CLIENT_CREDENTIALS, TEST_APP_CLIENT_ID
from apps.dot_ext.constants import CLIENT_ASSERTION_TYPE_VALUE

# The v3 token endpoint. This MUST be identical everywhere it appears: it is both
# the URL we POST to and the `aud` claim inside the client_assertion, which the
# token endpoint validates for an exact match (see _validate_authorization_jwt).
BB2_TOKEN_URL = os.getenv('BB2_TOKEN_URL', 'http://localhost:8000/v3/o/token')

# The key id advertised in the testclient's self-hosted JWKS and stamped on the
# client_assertion header. Must match apps.testclient.cc_selftest.TESTCLIENT_CC_KID.
TESTCLIENT_CC_KID = f'bb2-{os.getenv("TARGET_ENV", "local")}-cc-1'
DAMON_MYCHART_PHONE_NUMBER = '6082113314'
OTP_CODE = '123456'

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


def generate_pkce_data() -> tuple:
    """
    Generates a code verifier and code challenge for the PKCE flow.

    Returns:
        tuple: A tuple containing the code verifier and code challenge.
    """
    # Generate a random code verifier
    code_verifier = secrets.token_urlsafe(64)

    # Generate the code challenge using SHA256 and base64url encoding
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('ascii')).digest()).decode('ascii').rstrip('=')
    )

    return code_verifier, code_challenge


def get_clear_authorization_code(code_challenge: str) -> str:
    """
    Retrieves the authorization code from the Clear integration.

    Returns:
        str: The authorization code.
    """
    driver = webdriver.Chrome()

    # Start with building the url
    clear_login_url = f'https://verified.clearme.com/integrations/oauth2/auth?response_type=code&client_id=bluebutton-sample&state=teststate&redirect_uri=http://localhost:3001/api/clear/callback&scope=offline%20openid%20offline_access&code_challenge={code_challenge}&code_challenge_method=S256'

    # Simulate the user login and authorization flow
    driver.get(clear_login_url)

    driver.implicitly_wait(10)  # Wait for the page to load

    phone_input = driver.find_element(By.XPATH, '//input[@placeholder="Phone"]')
    phone_input.send_keys(DAMON_MYCHART_PHONE_NUMBER)

    time.sleep(3)  # Wait for a few seconds before clicking the continue button

    continue_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Continue')]")
    continue_button.click()

    time.sleep(3)  # Wait for a few seconds after clicking the continue button

    agree_and_continue_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Agree & Continue')]")
    agree_and_continue_button.click()

    time.sleep(3)

    code_input = driver.find_element(By.XPATH, '//input[@placeholder="Enter your Code"]')
    code_input.send_keys(OTP_CODE)

    time.sleep(3)

    skip_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Skip')]")
    skip_button.click()

    time.sleep(20)

    url = driver.current_url

    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)

    authorization_code = query_params.get('code', [None])[0]
    return authorization_code


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
        'aud': BB2_TOKEN_URL,
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
    url = BB2_TOKEN_URL
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'client_assertion': client_assertion,
        'client_assertion_type': client_assertion_type,
        'grant_type': grant_type,
        'scope': scope,
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response


def test_clear_integration_flow():
    code_verifier, code_challenge = generate_pkce_data()
    # Use selenium to simulate the user login and authorization flow to get the authorization code
    auth_code = get_clear_authorization_code(code_challenge)

    # TODO: Replace with actual env var name
    client_secret = os.getenv('CLEAR_CLIENT_SECRET', 'your_client_secret_here')
    id_token = get_clear_id_token(client_secret, auth_code, code_verifier)

    ial_payload = construct_ial_payload(id_token)

    # Long term we want to manage our own private key in SSM
    private_key = os.getenv('PRIVATE_KEY', 'your_private_key_here')
    client_assertion = jwt.encode(
        ial_payload,
        private_key,
        algorithm='RS384',
        headers={'kid': TESTCLIENT_CC_KID, 'typ': 'JWT'},
    )

    # Make the call to the token endpoint with the client_assertion and other params to get back access_token and refresh_token
    client_assertion_type = CLIENT_ASSERTION_TYPE_VALUE
    grant_type = CLIENT_CREDENTIALS
    scope = 'patient/ExplanationOfBenefit.rs patient/Patient.rs patient/Coverage.rs'

    access_token_response = get_access_token_response(client_assertion, client_assertion_type, grant_type, scope)

    assert access_token_response.status_code == 200, (
        f'Expected status code 200, got {access_token_response.status_code}'
    )

    access_token_response_json = access_token_response.json()

    assert 'access_token' in access_token_response_json, 'Access token not found in response'
    assert 'refresh_token' in access_token_response_json, 'Refresh token not found in response'
