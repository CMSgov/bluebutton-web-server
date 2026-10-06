import datetime
import logging
from datetime import timezone

# from unittest.mock import MagicMock, patch
import jwt
import pytest

# from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase

# from freezegun import freeze_time
from oauthlib.oauth2.rfc6749.errors import InvalidRequestError
from waffle.testutils import override_switch

from apps.dot_ext.constants import ASYMMETRIC_AUTH_REQUIRED_CLAIM_FIELDS, CAN_REQUIRED_CLAIM_FIELDS
from apps.dot_ext.validators import (
    AsymmetricAuthValidator,
    CMSAlignedNetworksValidator,
    validate_url,
)
from apps.logging.constants import HHS_SERVER_LOGNAME_FMT

ASYMMETRIC_AUTH_PAYLOAD = {
    'iss': 'test-client-id',
    'sub': 'test-client-id',
    'aud': 'payload',
    'jti': 'payload',
    'exp': datetime.datetime.now(timezone.utc).timestamp(),
}
EXTENSIONS_PAYLOAD = {
    'extensions': {
        'cms_smart': {
            'version': '1',
            'purpose_of_use': 'PATRQT',
            'id_token': 'alksjdlksajdlskajdskladsksdalkdsakldaskldaskljadsj',
        }
    }
}
CMS_ALIGNED_NETWORKS_PAYLOAD = {**ASYMMETRIC_AUTH_PAYLOAD, **EXTENSIONS_PAYLOAD}
log = logging.getLogger(HHS_SERVER_LOGNAME_FMT.format(__name__))


class ValidateURLTests(TestCase):
    def test_valid_urls(self):
        valid_urls = [
            'https://example.com',
            'https://foo.bar/baz',
            'https://sub.domain.co.uk/path?query=1',
        ]
        for url in valid_urls:
            try:
                validate_url(url)
            except ValidationError:
                self.fail(f'validate_url() raised ValidationError unexpectedly for {url}')

    def test_invalid_urls(self):
        invalid_urls = [
            'not-a-url',
            'example',
            'http://',
            '://example.com',
            'javascript:alert(document.cookie)',
            'javascript:alert(document.domain)',
            'https://localhost',
            'http://localhost',
            ' ',
        ]
        for url in invalid_urls:
            with self.assertRaises(ValidationError, msg=f'Expected failure for {url}'):
                validate_url(url)

    def test_empty_value_allowed(self):
        """Empty values should pass without raising error"""
        try:
            validate_url('')
            validate_url(None)
        except ValidationError:
            self.fail('validate_url() raised ValidationError for empty value')


@pytest.mark.parametrize(
    'validator_class, expected_fields',
    [
        (AsymmetricAuthValidator, ASYMMETRIC_AUTH_REQUIRED_CLAIM_FIELDS),
        (CMSAlignedNetworksValidator, CAN_REQUIRED_CLAIM_FIELDS),
    ],
)
def test_get_required_fields(validator_class, expected_fields):
    """Test that the validator returns the correct required fields."""
    validator = validator_class()
    assert validator.get_required_fields() == expected_fields


@pytest.mark.parametrize(
    'validator_class, waffle_switch',
    [
        (AsymmetricAuthValidator, 'asymmetric_auth_validation'),
        (CMSAlignedNetworksValidator, 'client_credentials_validation'),
    ],
)
def test_get_waffle_switch(validator_class, waffle_switch):
    """Test that the validator returns the correct waffle switch."""
    validator = validator_class()
    assert validator.get_waffle_switch() == waffle_switch


# @pytest.mark.django_db
# @pytest.mark.parametrize(
#     'validator_class, location, missing_field, target_value, expected_error_message',
#     [
#         (AsymmetricAuthValidator, 'payload', 'iss', None, 'Missing required field: iss'),
#         (AsymmetricAuthValidator, 'payload', 'sub', None, 'Missing required field: sub'),
#         (AsymmetricAuthValidator, 'payload', 'aud', None, 'Missing required field: aud'),
#         (AsymmetricAuthValidator, 'payload', 'jti', None, 'Missing required field: jti'),
#         (AsymmetricAuthValidator, 'payload', 'exp', None, 'Missing required field: exp'),
#         (CMSAlignedNetworksValidator, 'payload', 'iss', None, 'Missing required field: iss'),
#         (CMSAlignedNetworksValidator, 'payload', 'sub', None, 'Missing required field: sub'),
#         (CMSAlignedNetworksValidator, 'payload', 'aud', None, 'Missing required field: aud'),
#         (CMSAlignedNetworksValidator, 'payload', 'jti', None, 'Missing required field: jti'),
#         (CMSAlignedNetworksValidator, 'payload', 'exp', None, 'Missing required field: exp'),
#         (CMSAlignedNetworksValidator, 'payload', 'extension', None, 'Missing required field: extension'),
#         (AsymmetricAuthValidator, 'header', 'kid', None, 'Missing required field: kid'),
#         (AsymmetricAuthValidator, 'header', 'typ', None, 'Missing required field: typ'),
#         (CMSAlignedNetworksValidator, 'header', 'kid', None, 'Missing required field: kid'),
#         (CMSAlignedNetworksValidator, 'header', 'typ', None, 'Missing required field: typ'),
#         (AsymmetricAuthValidator, 'header', 'typ', 'invalid-jwt', 'Malformed JWT'),
#         (CMSAlignedNetworksValidator, 'header', 'typ', 'invalid-jwt', 'Malformed JWT'),
#     ],
# )
# @patch('apps.dot_ext.validators.jwt.decode_complete')
# @override_switch('asymmetric_auth_validation', active=True)
# @override_switch('client_credentials_validation', active=True)
# def test_shared_fields_validation_returns_invalid_request_error(
#     validator_class, location, missing_field, target_value, expected_error_message, caplog
# ):
#     """Test that missing required fields raise an InvalidRequestError."""
#     # Headers are the same for both validators
#     header_templates = {'typ': 'JWT', 'kid': 'some-kid'}
#     header = header_templates.copy()
#     payload_templates = {
#         AsymmetricAuthValidator: ASYMMETRIC_AUTH_PAYLOAD,
#         CMSAlignedNetworksValidator: CMS_ALIGNED_NETWORKS_PAYLOAD,
#     }
#     payload = payload_templates[validator_class].copy()

#     if location == 'header':
#         target_dic = header
#     else:
#         target_dic = payload

#     if target_value is None:
#         target_dic.pop(missing_field, None)
#     else:
#         # Make a bad value for the target field
#         target_dic[missing_field] = target_value

#     validator = validator_class()
#     mock_jwk = MagicMock()
#     dummy_jwks_client = MagicMock()

#     dummy_jwks_client.get_signing_key_from_jwt.return_value = mock_jwk

#     token = jwt.encode(payload, 'secret', algorithm='RS384')

#     with caplog.at_level(logging.WARNING):
#         with pytest.raises(InvalidRequestError):
#             validator._decode_and_validate_token(token, 'client-id', dummy_jwks_client)
#     assert expected_error_message in caplog.text


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, jku, header',
    [
        (
            AsymmetricAuthValidator,
            'https://example.com/jwks.json',
            {'typ': 'JWT', 'kid': 'some-kid', 'jku': 'https://example.com/jwks.json'},
        ),
        (AsymmetricAuthValidator, 'https://example.com/jwks.json', {'typ': 'JWT', 'kid': 'some-kid'}),
    ],
)
@override_switch('asymmetric_auth_validation', active=True)
def test_validate_jku_successful(validator_class, jku, header):
    """Test the validation of the 'jku' header field for successful cases."""
    validator = validator_class()
    token = jwt.encode(ASYMMETRIC_AUTH_PAYLOAD.copy(), 'secret', algorithm='HS256', headers=header)

    # Should not raise an error
    response = validator._validate_jku(token, jku)
    assert response is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, jku',
    [
        (AsymmetricAuthValidator, 'random'),
    ],
)
@override_switch('asymmetric_auth_validation', active=True)
def test_validate_jku_unsuccessful(validator_class, jku):
    """Test the validation of the 'jku' header field does not accept a mismatched JWKS URL."""
    validator = validator_class()
    header = {'typ': 'JWT', 'kid': 'some-kid', 'jku': 'not-a-valid-url'}
    token = jwt.encode(ASYMMETRIC_AUTH_PAYLOAD.copy(), 'secret', algorithm='HS256', headers=header)

    # Should raise an error
    with pytest.raises(InvalidRequestError):
        validator._validate_jku(token, jku)


def test_validate_time_comparison_successful():
    """Test the successful comparison of time-related fields."""
    # Set auth time to be 3 minutes ago
    validator = CMSAlignedNetworksValidator()
    mock_payload = {'auth_time': datetime.datetime.now(timezone.utc).timestamp() - 180}
    response = validator._validate_time_comparison(mock_payload, 'auth_time', 300)
    assert response is True


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, mock_payload, claim_key, time_window',
    [
        (
            CMSAlignedNetworksValidator,
            {'auth_time': "I'm a string"},
            'auth_time',
            300,
        ),
        (
            CMSAlignedNetworksValidator,
            {'iat': "I'm a string"},
            'iat',
            300,
        ),
        (
            CMSAlignedNetworksValidator,
            {'auth_time': datetime.datetime.now(timezone.utc).timestamp() + 60},
            'auth_time',
            300,
        ),
        (
            CMSAlignedNetworksValidator,
            {'iat': datetime.datetime.now(timezone.utc).timestamp() + 60},
            'iat',
            300,
        ),
        (
            CMSAlignedNetworksValidator,
            {'auth_time': datetime.datetime.now(timezone.utc).timestamp() - 301},
            'auth_time',
            300,
        ),
        (
            CMSAlignedNetworksValidator,
            {'iat': datetime.datetime.now(timezone.utc).timestamp() - 301},
            'iat',
            300,
        ),
    ],
)
def test_validate_time_comparison_unsuccessful(validator_class, mock_payload, claim_key, time_window):
    """Test the unsuccessful comparison of time-related fields."""
    validator = validator_class()
    with pytest.raises(InvalidRequestError):
        validator._validate_time_comparison(mock_payload, claim_key, time_window)
