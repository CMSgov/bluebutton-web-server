from http import HTTPStatus

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from django.urls import reverse
from waffle.testutils import override_switch

from apps.constants import (
    AUTH_SIGNING_ALG_ES384,
    CLIENT_CONFIDENTIAL_ASYMMETRIC,
    CLIENT_CREDENTIALS,
    CLIENT_CREDENTIALS_ACCEPTED_JWT_ALGORITHMS,
    PRIVATE_KEY_JWT,
)
from apps.wellknown.constants import SCOPES_SUPPORTED_V3_ONLY
from apps.wellknown.views.jwks import _local_private_keys

pytestmark = pytest.mark.django_db


def _private_key_pem(private_key) -> bytes:
    # Returns an RSA or EC private key as unencrypted PKCS#8 PEM, the form JWKS_PRIVATE_KEY_PEM and jwt.encode() take
    return private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


class TestOpenIDConnectConfiguration:
    """
    Test OpenIDConnectConfiguration URI
    """

    def test_valid_response(self, client, settings):
        """
        Valid User can login
        """
        response = client.get(reverse('openid-configuration'))
        assert response.status_code == HTTPStatus.OK
        body = response.content.decode()
        assert reverse('oauth2_provider_v2:token-v2') in body
        assert reverse('openid_connect_userinfo_v2') in body
        assert 'response_types_supported' in body
        assert settings.HOSTNAME_URL in body
        assert isinstance(response.json(), dict)


class TestSmartConfigurationV3:
    """
    Test SMART Configuration V3
    """

    @pytest.fixture
    def url(self):
        return reverse('smart_configuration_v3')

    @override_switch('v3_endpoints', active=True)
    def test_v3_config_fields(self, client, url):
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK
        data = response.json()

        assert CLIENT_CREDENTIALS in data.get('grant_types_supported', [])
        assert CLIENT_CONFIDENTIAL_ASYMMETRIC in data.get('capabilities', [])
        assert data.get('token_endpoint_auth_methods_supported') == [PRIVATE_KEY_JWT]
        assert (
            data.get('token_endpoint_auth_signing_alg_values_supported') == CLIENT_CREDENTIALS_ACCEPTED_JWT_ALGORITHMS
        )

    @override_switch('v3_endpoints', active=True)
    @override_switch('enable_auditevents', active=False)
    def test_v3_config_auditevent_scopes_hidden_when_switch_disabled(self, client, url):
        """
        Note that this can be removed when the auditevents switch is removed
        """
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK
        data = response.json()

        for scope in SCOPES_SUPPORTED_V3_ONLY:
            assert scope not in data.get('scopes_supported', [])

    @override_switch('v3_endpoints', active=True)
    @override_switch('enable_auditevents', active=True)
    def test_v3_config_auditevent_scopes_shown_when_switch_enabled(self, client, url):
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK
        data = response.json()

        for scope in SCOPES_SUPPORTED_V3_ONLY:
            assert scope in data.get('scopes_supported', [])


class TestJwksJson:
    @pytest.fixture(autouse=True)
    def _isolated_jwks(self, monkeypatch):
        # _local_jwks is cached and the view reads env vars, so reset both after each test
        # the autouse=True makes pytest run this automatically for each testcase in this class
        # monkeypatch mimics what unittest.patch had been doing before. This forcibly sets the env var to empty string.
        # yield is where the test runs. Prior to yield is set up and afterwards is tear down
        # since _local_jwks is built to try and reuse the same key pair, the clearing out of the cache needs to happen
        # to ensure that it does not leak over to other tests
        monkeypatch.setenv('JWKS_PUBLIC_KEY_PEM', '')
        yield
        _local_private_keys.cache_clear()

    @pytest.fixture
    def url(self):
        return reverse('jwks-json')

    def test_local_serves_public_jwks(self, client, url, settings):
        settings.TARGET_ENV = 'local'
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK
        keys = response.json()['keys']
        assert [k['alg'] for k in keys] == CLIENT_CREDENTIALS_ACCEPTED_JWT_ALGORITHMS
        for key in keys:
            assert key['kty'] == ('EC' if key['alg'] == AUTH_SIGNING_ALG_ES384 else 'RSA')
            assert 'kid' in key
            assert 'd' not in key  # this ensures it is not a private key
        assert len({k['kid'] for k in keys}) == len(keys)

    def test_local_jwks_verifies_signed_jwt(self, client, url, settings, monkeypatch):
        settings.TARGET_ENV = 'local'
        rsa_pem = _private_key_pem(rsa.generate_private_key(public_exponent=65537, key_size=2048))
        ec_pem = _private_key_pem(ec.generate_private_key(ec.SECP384R1()))

        jwks_by_pem = {}
        for pem in (rsa_pem, ec_pem):
            monkeypatch.setenv('JWKS_PRIVATE_KEY_PEM', pem.decode())
            _local_private_keys.cache_clear()
            # getting the public keys from /.well-known/jwks.json
            keys = client.get(url).json()['keys']
            jwks_by_pem[pem] = {key['alg']: key for key in keys}

        # Sign with the private key for each algorithm, then verify with the matching public JWK served by the endpoint
        for alg in CLIENT_CREDENTIALS_ACCEPTED_JWT_ALGORITHMS:
            pem = ec_pem if alg == AUTH_SIGNING_ALG_ES384 else rsa_pem
            jwk = jwks_by_pem[pem][alg]
            token = jwt.encode({'iss': 'x'}, pem, algorithm=alg, headers={'kid': jwk['kid']})
            assert jwt.decode(token, jwt.PyJWK(jwk).key, algorithms=[alg])['iss'] == 'x'

    def test_non_local_without_configured_key_is_404(self, client, url, settings):
        settings.TARGET_ENV = 'prod'
        assert client.get(url).status_code == HTTPStatus.NOT_FOUND

    def test_configured_key_is_served(self, client, url, settings, monkeypatch):
        settings.TARGET_ENV = 'prod'
        monkeypatch.setenv('JWKS_PUBLIC_KEY_PEM', '{"keys": []}')
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {'keys': []}

    def test_post_not_allowed(self, client, url):
        assert client.post(url).status_code == HTTPStatus.METHOD_NOT_ALLOWED
