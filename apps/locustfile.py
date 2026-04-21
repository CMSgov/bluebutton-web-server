# locustfile.py
import base64
import hashlib
import os
import random
import secrets
from urllib.parse import parse_qs, urlparse

from locust import HttpUser, between, task
from versions import Versions

"""
Locust load test for bluebutton-web-server running in Fargate (TEST env).

Simulates:
- OAuth2 authorization_code flow via /{version}/o/authorize/ and /{version}/o/token/
- FHIR calls via /v{version}/fhir/ExplanationOfBenefit and /v{version}/fhir/Patient
- Basic HTML page access (/, /docs/)

Environment variables:
- BB_CLIENT_ID, BB_CLIENT_SECRET, BB_REDIRECT_URI
- BB_SCOPE
- BB_USERNAME, BB_PASSWORD
"""

BB_CLIENT_ID = os.getenv('BB_CLIENT_ID', 'client-id-here')
BB_CLIENT_SECRET = os.getenv(
    'BB_CLIENT_SECRET',
    'client-secret-here',
)
BB_REDIRECT_URI = os.getenv('BB_REDIRECT_URI', 'callback-here')
BB_SCOPE = os.getenv('BB_SCOPE', 'profile patient/ExplanationOfBenefit.read patient/Patient.read patient/Coverage.read')
BB_USERNAME_ENV = os.getenv('BB_USERNAME')
BB_PASSWORD_ENV = os.getenv('BB_PASSWORD')


def generate_credentials():
    """Return a tuple (username, password) where the username is
    `BBUser` + 5-digit zero-padded number and the password is `PW` + same
    number + `!`.
    """
    n = random.randint(0, 9999)
    s = f'{n:05d}'
    return f'BBUser{s}', f'PW{s}!'


def make_pkce_pair():
    """Generate a PKCE code_verifier and code_challenge (S256).

    Returns (verifier, challenge) as strings.
    """
    # generate a high-entropy random verifier
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode('ascii')
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
    return verifier, challenge


def get_state():
    # Server enforces minimum state length; use high-entropy value.
    return secrets.token_urlsafe(24)


class BlueButtonUser(HttpUser):
    """
    Simulated Blue Button web-server user:
    - Visits home/docs
    - Performs OAuth2 auth code flow
    - Calls FHIR resources with the obtained access token
    """

    wait_time = between(1, 5)
    access_token = None
    api_version = None

    def on_start(self):
        """Use the class's `api_version` when provided, otherwise pick one.

        Subclasses can set `api_version` at class level to ensure each
        Locust user class targets a specific API version.
        """
        if self.api_version is None:
            self.api_version = random.choice(Versions.supported_versions())

        # Determine credentials for this simulated user. Prefer explicit
        # environment variables if both are provided; otherwise generate
        # a random matching pair (BBUser##### / PW#####!).
        if BB_USERNAME_ENV and BB_PASSWORD_ENV:
            self.username = BB_USERNAME_ENV
            self.password = BB_PASSWORD_ENV
        else:
            self.username, self.password = generate_credentials()

        # PKCE pair for this user session
        self.code_verifier, self.code_challenge = make_pkce_pair()

        self._authorize_and_get_token()

    def _version_prefix(self):
        return f'/{Versions.as_str(self.api_version)}'

    def _authorize_and_get_token(self):
        state = get_state()
        auth_data = {
            'client_id': BB_CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': BB_REDIRECT_URI,
            'scope': BB_SCOPE,
            'state': state,
            'code_challenge': getattr(self, 'code_challenge', None),
            'code_challenge_method': 'S256',
        }
        prefix = self._version_prefix()
        code = None

        # Step 1: POST authorize directly (endpoint reachability check)
        with self.client.post(
            f'{prefix}/o/authorize/',
            data=auth_data,
            name='oauth_authorize_post',
            allow_redirects=False,
            catch_response=True,
        ) as resp:
            # Treat common OAuth responses as success for endpoint reachability.
            if resp.status_code in (200, 302, 303):
                redirect_location = resp.headers.get('Location', '')

                # If auth code is present, continue to token exchange.
                if redirect_location:
                    parsed = urlparse(redirect_location)
                    query = parse_qs(parsed.query)
                    code = query.get('code', [None])[0]
                    returned_state = query.get('state', [None])[0]

                    if code and returned_state != state:
                        resp.failure('State mismatch in authorize redirect')
                        return

                resp.success()
            else:
                resp.failure(f'Authorize POST failed: {resp.status_code}')
                return

        # Step 2: Exchange authorization code for token (only when present)
        if not code:
            self.access_token = None
            return

        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': BB_REDIRECT_URI,
            'client_id': BB_CLIENT_ID,
            'client_secret': BB_CLIENT_SECRET,
            'code_verifier': getattr(self, 'code_verifier', None),
        }

        token_resp = self.client.post(
            f'{prefix}/o/token/',
            data=token_data,
            name='oauth_token',
        )

        if token_resp.status_code == 200:
            json_data = token_resp.json()
            self.access_token = json_data.get('access_token')
        else:
            self.access_token = None

    def _auth_headers(self):
        if self.access_token:
            return {'Authorization': f'Bearer {self.access_token}'}
        return {}

    @task(1)
    def home_page(self):
        self.client.get('/', name='home_page')

    @task(1)
    def docs_page(self):
        self.client.get(
            'https://bluebutton.cms.gov/api-documentation/',
            name='docs_page',
        )

    @task(3)
    def fhir_explanation_of_benefit(self):
        """FHIR ExplanationOfBenefit list call for the logged-in bene."""
        headers = self._auth_headers()
        if not headers:
            return
        self.client.get(
            f'{self._version_prefix()}/fhir/ExplanationOfBenefit',
            headers=headers,
            name='fhir_eob_list',
        )

    @task(2)
    def fhir_patient(self):
        """FHIR Patient resource for the current bene."""
        headers = self._auth_headers()
        if not headers:
            return
        self.client.get(
            f'{self._version_prefix()}/fhir/Patient',
            headers=headers,
            name='fhir_patient',
        )


class BlueButtonUserV1(BlueButtonUser):
    """Locust user that targets API v1."""

    api_version = Versions.V1
    weight = 1


class BlueButtonUserV2(BlueButtonUser):
    """Locust user that targets API v2."""

    api_version = Versions.V2
    weight = 1


class BlueButtonUserV3(BlueButtonUser):
    """Locust user that targets API v3."""

    api_version = Versions.V3
    weight = 1
