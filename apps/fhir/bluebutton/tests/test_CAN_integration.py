import base64
import hashlib
import os
import secrets
import time
import urllib
import uuid
from urllib.parse import urlencode

import jwt
import pytest
import requests
from django.contrib.auth.models import Group
from django.test.client import Client
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from waffle.testutils import override_switch

from apps.constants import (
    CLIENT_CREDENTIALS,
    COVERAGE_SCOPE,
    EOB_SCOPE,
    PATIENT_SCOPE,
    TEST_APP_CLIENT_ID,
    TEST_APP_CLIENT_SECRET,
)
from apps.dot_ext.constants import CLIENT_ASSERTION_TYPE_VALUE, CLIENT_CREDENTIALS_TYPE

# The v3 token endpoint. This MUST be identical everywhere it appears: it is both
# the URL we POST to and the `aud` claim inside the client_assertion, which the
# token endpoint validates for an exact match (see _validate_authorization_jwt).
# You can export the token endpoint URL in the container so that it can be used in the test.
# This is useful for testing with a pre-existing app.
# i.e. `export BB2_TOKEN_URL="http://localhost:8000/v3/o/token"`
BB2_TOKEN_URL = os.getenv('BB2_TOKEN_URL', 'http://localhost:8000/v3/o/token')
# You can export the app client id in the container so that it can be used in the test.
# This is useful for testing with a pre-existing app.
# i.e. `export APP_CLIENT_ID="your_app_client_id"`
APP_CLIENT_ID = os.getenv('APP_CLIENT_ID')
# You can export a false value for this flag in the container to use the requests library rather than the Django test client.
# This is useful for testing with a pre-existing app.
# i.e. `export ENABLE_CLIENT="false"`
ENABLE_CLIENT = os.getenv('ENABLE_CLIENT', 'true')

DAMON_MYCHART_PHONE_NUMBER = '6082113314'
OTP_CODE = '123456'
CLEAR_REDIRECT_URI = 'http://localhost:3001/api/clear/callback'
CLEAR_CLIENT_ID = os.getenv('CLEAR_CLIENT_ID')
CLEAR_CLIENT_SECRET = os.getenv('CLEAR_CLIENT_SECRET')
CAN_PRIVATE_KEY = os.getenv('CAN_PRIVATE_KEY')
# The key id advertised in the testclient's self-hosted JWKS and stamped on the
# client_assertion header.
TEST_APP_KID = 'my-key-id-1'

# Convert the raw string to a boolean for easier use in the test
is_client_enabled = ENABLE_CLIENT.lower() == 'true'


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


def find_element_and_click(wait: WebDriverWait, by_method: str, locator_value: str) -> None:
    """
    Finds the element on the page and clicks on it.

    Args:
        wait (WebDriverWait): The wait object that defines how long to look for the element before timing out.
        by_method (str): The method we are using to find the element (text, name, xpath, etc.)
        locator_value (str): The specific value we are looking for.

    Raises:
        NoSuchElementException error
    """
    try:
        element = wait.until(EC.presence_of_element_located((by_method, locator_value)))
        element.click()
    except NoSuchElementException:
        print(f'Failed to click {locator_value}.')


def find_element_and_send_keys(wait: WebDriverWait, by_method: str, locator_value: str, input_text: str) -> None:
    """
    Finds the element on the page and type data inside it.

    Args:
        wait (WebDriverWait): The wait object that defines how long to look for the element before timing out.
        by_method (str): The method we are using to find the element (text, name, xpath, etc.)
        locator_value (str): The specific value we are looking for.
        input_text (str): The text to type within the element.

    Raises:
        NoSuchElementException error
    """
    try:
        element = wait.until(EC.presence_of_element_located((by_method, locator_value)))
        element.send_keys(input_text)
    except NoSuchElementException:
        print(f'Failed to send keys to {locator_value}.')


def get_clear_authorization_code(driver: webdriver.Chrome, client_id: str, code_challenge: str) -> str:
    """
    Retrieves the authorization code from the Clear integration.

    Args:
        driver (WebDriver): The WebDriver instance.
        client_id (str): The client ID for the Clear integration.
        code_challenge (str): The code challenge generated for the PKCE flow.

    Returns:
        str: The authorization code.
    """
    # See here for building the url: https://docs.clearme.com/docs/individual-access-token
    clear_login_url = f'https://verified.clearme.com/integrations/oauth2/auth?response_type=code&client_id={client_id}&state=teststate&redirect_uri={CLEAR_REDIRECT_URI}&scope=offline%20openid%20offline_access&code_challenge={code_challenge}&code_challenge_method=S256'

    # Simulate the user login and authorization flow
    driver.get(clear_login_url)
    # We use WebDriverWait so that we don't have to put manual sleeps in between each action
    # Usually XPATH was the most reliable way to get the object from the screen
    wait = WebDriverWait(driver, 20)
    find_element_and_send_keys(
        wait=wait,
        by_method=By.NAME,
        locator_value='phone',
        input_text=DAMON_MYCHART_PHONE_NUMBER,
    )
    find_element_and_click(
        wait=wait,
        by_method=By.XPATH,
        locator_value='//button[contains(text(), "Continue")]',
    )
    find_element_and_click(
        wait=wait,
        by_method=By.XPATH,
        locator_value='//button[contains(text(), "Agree & Continue")]',
    )
    # This sleep seems to be necessary because sometimes it loads too quickly and stalls.
    time.sleep(2)
    find_element_and_send_keys(
        wait=wait,
        by_method=By.XPATH,
        locator_value='//input[@aria-label="6 Digit Code"]',
        input_text=OTP_CODE,
    )
    # This sleep seems to be necessary because sometimes it loads too quickly and stalls.
    time.sleep(2)

    # Can't use skip_button.click() because it's a hidden element, so have to use execute_script instead.
    skip_button = wait.until(EC.presence_of_element_located((By.XPATH, '//button[contains(text(), "Skip")]')))
    driver.execute_script('arguments[0].click();', skip_button)

    try:
        # Need to wait until code gets generated in url before proceeding
        wait.until(EC.url_contains('code'))
    except NoSuchElementException:
        print('The code was not found on this page')

    url = driver.current_url

    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)

    authorization_code = query_params.get('code', [None])[0]
    return authorization_code


def get_clear_id_token(client_id: str, client_secret: str, code: str, code_verifier: str) -> str:
    """
    Exchanges the authorization code for an ID token from Clear.

    Args:
        client_id (str): The client ID for the Clear integration.
        client_secret (str): The client secret for the Clear integration.
        code (str): The authorization code received from Clear.
        code_verifier (str): The code verifier used in the PKCE flow.

    Returns:
        str: The ID token received from Clear.
    """
    # See here for building the post request: https://docs.clearme.com/docs/individual-access-token
    url = 'https://verified.clearme.com/integrations/oauth2/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'offline openid offline_access',
        'grant_type': 'authorization_code',
        'redirect_uri': CLEAR_REDIRECT_URI,
        'code': code,
        'code_verifier': code_verifier,
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json().get('id_token')


def construct_ial_payload(id_token: str, app_client_id: str) -> dict:
    """
    Constructs the payload for the IAL (Identity Assurance Level) request to the Blue Button API token endpoint.

    Args:
        id_token (str): The ID token received from Clear.
        app_client_id (str): The client ID of the application.

    Returns:
        dict: A dictionary representing the payload for the IAL request.
    """
    return {
        'iss': app_client_id,
        'sub': app_client_id,
        'aud': BB2_TOKEN_URL,
        'jti': str(uuid.uuid4()),  # Randomly generated uuid
        'exp': int(time.time()) + 300,  # Current time + 5 minutes (300 seconds)
        'extensions': {'cms_smart': {'version': '1', 'purpose_of_use': 'PATRQT', 'id_token': id_token}},
    }


def get_payload(driver: webdriver.Chrome, app_client_id: str, scope: str) -> dict:
    """
    Generates the payload for the access token request to the Blue Button API token endpoint.

    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance used for browser automation.
        app_client_id (str): The client ID of the application.
        scope (str): The scope for which the access token is requested.

    Returns:
        dict: A dictionary representing the payload for the access token request.
    """
    code_verifier, code_challenge = generate_pkce_data()

    # Use selenium to simulate the user login and authorization flow to get the authorization code
    auth_code = get_clear_authorization_code(driver, CLEAR_CLIENT_ID, code_challenge)
    # Exchange code for id token
    id_token = get_clear_id_token(CLEAR_CLIENT_ID, CLEAR_CLIENT_SECRET, auth_code, code_verifier)
    ial_payload = construct_ial_payload(id_token, app_client_id)

    # Use the private key to sign the payload and create a client_assertion JWT
    client_assertion = jwt.encode(
        ial_payload,
        CAN_PRIVATE_KEY,
        algorithm='RS384',
        headers={'kid': TEST_APP_KID, 'typ': 'JWT'},
    )

    client_assertion_type = CLIENT_ASSERTION_TYPE_VALUE
    grant_type = CLIENT_CREDENTIALS

    return {
        'client_assertion': client_assertion,
        'client_assertion_type': client_assertion_type,
        'grant_type': grant_type,
        'scope': scope,
    }


def get_access_token_response(json_payload: dict) -> dict:
    """
    Exchanges the CAN request for an access token from the Blue Button API.

    Args:
        json_payload (dict): The JSON payload containing the token request parameters.

    Returns:
        dict: A dictionary containing the access token and other related information.
    """
    if is_client_enabled:
        client = Client()
        url = '/v3/o/token'

        response = client.post(
            url,
            data=urlencode(json_payload),
            content_type='application/x-www-form-urlencoded',
        )
        return response
    else:
        url = BB2_TOKEN_URL
        custom_headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        response = requests.post(url, data=urlencode(json_payload), headers=custom_headers)
        return response


@pytest.mark.skipif(os.getenv('CAN_INTEGRATION_TEST') != 'true', reason='Selenium tests disabled')
@pytest.mark.integration
@pytest.mark.django_db
@override_switch('client_credentials_validation', active=True)
@override_switch('v3_endpoints', active=True)
def test_clear_integration_flow(driver, basic_user, create_application, create_capability):
    """
    Integration test specifically against clear that does the following:
     - Runs through the auth process with a synth user in CLEAR to generate a valid IAL JWT (via selenium)
     - Generates an authorization JWT that contains the IAL JWT, using the test-app that is auto built into the app
     - Runs through the auth process in Blue Button using the authorization JWT
    """
    # Needed to add this otherwise it would fail when looking up groups in a later method
    Group.objects.create(name='BlueButton')
    # Set up basic user, capability, and application
    user = basic_user()
    eob_capability = create_capability(name=EOB_SCOPE, urls=[['GET', '/v[3]/fhir/ExplanationOfBenefit[/]?$']])
    coverage_capability = create_capability(name=COVERAGE_SCOPE, urls=[['GET', '/v[3]/fhir/Coverage[/]?$']])
    patient_capability = create_capability(name=PATIENT_SCOPE, urls=[['GET', '/v[3]/fhir/Patient[/]?$']])
    application = create_application(
        name='test',
        grant_type='client-credentials',
        user=user,
        allowed_auth_type=CLIENT_CREDENTIALS_TYPE,
        jwks_uri='http://localhost:8000/.well-known/jwks.json',
        client_id=TEST_APP_CLIENT_ID,
        client_secret=TEST_APP_CLIENT_SECRET,
    )
    application.scope.add(eob_capability)
    application.scope.add(coverage_capability)
    application.scope.add(patient_capability)
    if APP_CLIENT_ID:
        app_client_id = APP_CLIENT_ID
    else:
        app_client_id = application.client_id
    combined_scopes = f'{EOB_SCOPE} {COVERAGE_SCOPE} {PATIENT_SCOPE}'

    json_payload = get_payload(driver, app_client_id, combined_scopes)

    access_token_response = get_access_token_response(json_payload)

    assert access_token_response.status_code == 200, (
        f'Expected status code 200, got {access_token_response.status_code}'
    )

    access_token_response_json = access_token_response.json()

    assert 'access_token' in access_token_response_json, 'Access token not found in response'
    assert 'refresh_token' in access_token_response_json, 'Refresh token not found in response'
    scope = access_token_response_json.get('scope')
    # AuditEvent is also returned in the response from the requests library so don't do an exact assertion,
    # just check that the combined scopes are in the returned scope.
    assert combined_scopes in scope, f'Expected scope "{combined_scopes}" to be in response scope "{scope}"'
