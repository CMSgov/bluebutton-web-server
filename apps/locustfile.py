import csv
import os
import random
import re
from threading import Lock

from locust import HttpUser, between, task
from locust.exception import StopUser
from versions import Versions

"""
Token-fed Locust load test for bluebutton-web-server.

Simulates token-authenticated FHIR traffic for:
- /v{version}/fhir/ExplanationOfBenefit
- /v{version}/fhir/Coverage
- /v{version}/fhir/Patient

Provide versioned access token pools:
- Non-v3 pool (used by v1 and v2 users):
    - BB_ACCESS_TOKEN or BB_ACCESS_TOKEN_NON_V3
    - BB_ACCESS_TOKENS or BB_ACCESS_TOKENS_NON_V3
    - BB_ACCESS_TOKENS_FILE or BB_ACCESS_TOKENS_FILE_NON_V3
- v3 pool (used by v3 users):
    - BB_ACCESS_TOKEN_V3
    - BB_ACCESS_TOKENS_V3
    - BB_ACCESS_TOKENS_FILE_V3

Optional:
- BB_TOKEN_SELECTION=random|round_robin (default: random)
"""

TOKEN_POOL_NON_V3 = 'non_v3'
TOKEN_POOL_V3 = 'v3'

# Backward-compatible aliases map existing env vars to the non-v3 pool.
BB_ACCESS_TOKEN_NON_V3 = os.getenv('BB_ACCESS_TOKEN_NON_V3', os.getenv('BB_ACCESS_TOKEN', '')).strip()
BB_ACCESS_TOKENS_NON_V3 = os.getenv('BB_ACCESS_TOKENS_NON_V3', os.getenv('BB_ACCESS_TOKENS', '')).strip()
BB_ACCESS_TOKENS_FILE_NON_V3 = os.getenv('BB_ACCESS_TOKENS_FILE_NON_V3', os.getenv('BB_ACCESS_TOKENS_FILE', '')).strip()

BB_ACCESS_TOKEN_V3 = os.getenv('BB_ACCESS_TOKEN_V3', '').strip()
BB_ACCESS_TOKENS_V3 = os.getenv('BB_ACCESS_TOKENS_V3', '').strip()
BB_ACCESS_TOKENS_FILE_V3 = os.getenv('BB_ACCESS_TOKENS_FILE_V3', '').strip()

BB_TOKEN_SELECTION = os.getenv('BB_TOKEN_SELECTION', 'random').strip().lower()

TOKEN_SPLIT_RE = re.compile(r'[\s,]+')
_TOKEN_LOCKS = {
    TOKEN_POOL_NON_V3: Lock(),
    TOKEN_POOL_V3: Lock(),
}
_TOKEN_INDICES = {
    TOKEN_POOL_NON_V3: 0,
    TOKEN_POOL_V3: 0,
}


def _parse_token_text(raw_text):
    return [token.strip() for token in TOKEN_SPLIT_RE.split(raw_text) if token.strip()]


def _load_tokens_from_file(file_path):
    if not file_path or not os.path.exists(file_path):
        return []

    with open(file_path, encoding='utf-8') as token_file:
        content = token_file.read().strip()

    if not content:
        return []

    first_line = content.splitlines()[0].strip().lower()
    if ',' in first_line and ('token' in first_line or 'access_token' in first_line):
        tokens = []
        with open(file_path, newline='', encoding='utf-8') as token_file:
            reader = csv.DictReader(token_file)
            for row in reader:
                token = (row.get('access_token') or row.get('token') or '').strip()
                if token:
                    tokens.append(token)
        return tokens

    tokens = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        tokens.extend(_parse_token_text(stripped))

    return tokens


def _dedupe_tokens(tokens):
    deduped = []
    seen = set()
    for token in tokens:
        if token not in seen:
            deduped.append(token)
            seen.add(token)
    return deduped


def _load_access_tokens(single_token, token_list, token_file):
    tokens = []

    if single_token:
        tokens.append(single_token)

    if token_list:
        tokens.extend(_parse_token_text(token_list))

    if token_file:
        tokens.extend(_load_tokens_from_file(token_file))

    return _dedupe_tokens(tokens)


ACCESS_TOKENS_BY_POOL = {
    TOKEN_POOL_NON_V3: _load_access_tokens(
        BB_ACCESS_TOKEN_NON_V3,
        BB_ACCESS_TOKENS_NON_V3,
        BB_ACCESS_TOKENS_FILE_NON_V3,
    ),
    TOKEN_POOL_V3: _load_access_tokens(
        BB_ACCESS_TOKEN_V3,
        BB_ACCESS_TOKENS_V3,
        BB_ACCESS_TOKENS_FILE_V3,
    ),
}


def _token_pool_for_version(version):
    if version == Versions.V3:
        return TOKEN_POOL_V3
    return TOKEN_POOL_NON_V3


def _next_access_token(pool_name):
    if pool_name not in ACCESS_TOKENS_BY_POOL:
        return None

    tokens = ACCESS_TOKENS_BY_POOL[pool_name]
    if not tokens:
        return None

    if BB_TOKEN_SELECTION == 'round_robin':
        with _TOKEN_LOCKS[pool_name]:
            token = tokens[_TOKEN_INDICES[pool_name] % len(tokens)]
            _TOKEN_INDICES[pool_name] += 1
            return token

    return random.choice(tokens)


class BlueButtonUser(HttpUser):
    """Simulated Blue Button API user using a pre-issued bearer token."""

    abstract = True
    wait_time = between(1, 5)
    access_token = None
    api_version = None

    def on_start(self):
        if self.api_version is None:
            # Base class represents a mixed-version population.
            self.api_version = random.choice(Versions.supported_versions())

        token_pool = _token_pool_for_version(self.api_version)
        self.access_token = _next_access_token(token_pool)
        if not self.access_token:
            if token_pool == TOKEN_POOL_V3:
                raise StopUser(
                    'No v3 access token supplied. Set BB_ACCESS_TOKEN_V3, BB_ACCESS_TOKENS_V3, or BB_ACCESS_TOKENS_FILE_V3.'
                )
            raise StopUser(
                'No non-v3 access token supplied. Set BB_ACCESS_TOKEN_NON_V3 (or BB_ACCESS_TOKEN), '
                'BB_ACCESS_TOKENS_NON_V3 (or BB_ACCESS_TOKENS), or BB_ACCESS_TOKENS_FILE_NON_V3 '
                '(or BB_ACCESS_TOKENS_FILE).'
            )

    def _version_prefix(self):
        return f'/{Versions.as_str(self.api_version)}'

    def _auth_headers(self):
        return {'Authorization': f'Bearer {self.access_token}'}

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
    def fhir_coverage(self):
        """FHIR Coverage list call for the logged-in bene."""
        headers = self._auth_headers()
        if not headers:
            return
        self.client.get(
            f'{self._version_prefix()}/fhir/Coverage',
            headers=headers,
            name='fhir_coverage_list',
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
