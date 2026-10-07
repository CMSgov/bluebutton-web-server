import datetime
import logging
import os
from datetime import timezone
from unittest.mock import MagicMock, patch

import jwt
import pytest
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase
from freezegun import freeze_time
from oauthlib.oauth2.rfc6749.errors import InvalidRequestError
from waffle.testutils import override_switch

from apps.dot_ext.constants import (
    ASYMMETRIC_AUTH_REQUIRED_CLAIM_FIELDS,
    CAN_REQUIRED_CLAIM_FIELDS,
    CLEAR_HIGHER_ISS,
    CLEAR_LOWER_ISS,
    IDME_HIGHER_ISS,
    IDME_LOWER_ISS,
)
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
VALID_IAL_JWT_PAYLOAD = {
    'iss': 'test_iss',
    'jti': 'test_validate_ial_jwt',
    'sub': 'test_sub',
    'aud': 'test_aud',
    'exp': datetime.datetime.now(timezone.utc).timestamp() + 300,
    'iat': datetime.datetime.now(timezone.utc).timestamp(),
    'auth_time': datetime.datetime.now(timezone.utc).timestamp() - 60,
    'identity_assurance_level': 2,
    'family_name': 'Doe',
    'given_name': 'John',
    'birthdate': '1990-01-01',
}
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
def test_validate_and_get_jwks_uri_successful(validator_class, jku, header):
    """Test the validation of the 'jku' header field for successful cases."""
    validator = validator_class()
    token = jwt.encode(ASYMMETRIC_AUTH_PAYLOAD.copy(), 'secret', algorithm='HS256', headers=header)

    # Should not raise an error
    response = validator._validate_and_get_jwks_uri(token, jku)
    assert response == jku


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, jku',
    [
        (AsymmetricAuthValidator, 'random'),
    ],
)
@override_switch('asymmetric_auth_validation', active=True)
def test_validate_and_get_jwks_uri_unsuccessful(validator_class, jku):
    """Test the validation of the 'jku' header field does not accept a mismatched JWKS URL."""
    validator = validator_class()
    header = {'typ': 'JWT', 'kid': 'some-kid', 'jku': 'not-a-valid-url'}
    token = jwt.encode(ASYMMETRIC_AUTH_PAYLOAD.copy(), 'secret', algorithm='HS256', headers=header)

    # Should raise an error
    with pytest.raises(InvalidRequestError):
        validator._validate_and_get_jwks_uri(token, jku)


def test_validate_time_comparison_successful():
    """Test the successful comparison of time-related fields."""
    validator = CMSAlignedNetworksValidator()
    # Set auth time to be 3 minutes ago
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


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, jti',
    [(CMSAlignedNetworksValidator, 'can_cache_replay'), (AsymmetricAuthValidator, 'asym_auth_cache_replay')],
)
@override_switch('client_credentials_validation', active=True)
@override_switch('asymmetric_auth_validation', active=True)
@patch('jwt.decode_complete')
def test_validate_and_decode_token_cache_successful(
    mock_decode_complete,
    validator_class,
    jti,
):
    """Test correct cache behavior for _validate_and_decode_token"""
    validator = validator_class()
    mock_jwks_client = MagicMock()
    mock_jwks_client.get_signing_key_from_jwt.return_value = MagicMock()
    with freeze_time() as frozen_time:
        # Don't modify the original CMS_ALIGNED_NETWORKS_PAYLOAD directly
        test_payload = CMS_ALIGNED_NETWORKS_PAYLOAD.copy()
        test_payload['jti'] = jti
        mock_decode_complete.return_value = {
            'payload': test_payload,
            'header': {'typ': 'JWT'},
        }

        result = validator._decode_and_validate_token('token', 'test_iss', mock_jwks_client)
        assert result == test_payload

        # Assert cache has the key we'd expect and that the result is what we'd expect
        cache_key = f'{test_payload.get("iss")}-{test_payload.get("jti")}'
        assert cache.get(cache_key) == 'sentinel'

        # Advance time by 300 seconds and assert cache no longer has key
        frozen_time.tick(delta=datetime.timedelta(seconds=300))
        assert cache.get(cache_key) is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, jti',
    [
        (CMSAlignedNetworksValidator, 'can_cache_replay'),
        (AsymmetricAuthValidator, 'asym_auth_cache_replay'),
    ],
)
@override_switch('client_credentials_validation', active=True)
@override_switch('asymmetric_auth_validation', active=True)
@patch('jwt.decode_complete')
def test_decode_and_validate_token_cache_replay_unsuccessful(
    mock_decode_complete,
    validator_class,
    jti,
):
    """Test _decode_and_validate_token fails on second cache hit with same iss/jti combo"""

    validator = validator_class()
    mock_jwks_client = MagicMock()
    mock_jwks_client.get_signing_key_from_jwt.return_value = MagicMock()
    # Don't modify the original CMS_ALIGNED_NETWORKS_PAYLOAD directly
    test_payload = CMS_ALIGNED_NETWORKS_PAYLOAD.copy()
    test_payload['jti'] = jti
    mock_decode_complete.return_value = {
        'payload': test_payload,
        'header': {'typ': 'JWT'},
    }

    result = validator._decode_and_validate_token('token', 'test_iss', mock_jwks_client)
    assert result == test_payload

    # Assert cache has the key we'd expect and that the result is what we'd expect
    cache_key = f'{test_payload.get("iss")}-{test_payload.get("jti")}'
    assert cache.get(cache_key) == 'sentinel'

    # Second call with same jti/iss fails
    with pytest.raises(InvalidRequestError):
        validator._decode_and_validate_token('token', 'test_iss', mock_jwks_client)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, header',
    [
        (CMSAlignedNetworksValidator, 'invalid-typ'),
        (AsymmetricAuthValidator, 'invalid-typ'),
    ],
)
@override_switch('client_credentials_validation', active=True)
@override_switch('asymmetric_auth_validation', active=True)
@patch('jwt.decode_complete')
def test_decode_and_validate_token_invalid_header(
    mock_decode_complete,
    validator_class,
    header,
):
    """Test _decode_and_validate_token fails with invalid typ in header"""

    validator = validator_class()
    mock_jwks_client = MagicMock()
    mock_jwks_client.get_signing_key_from_jwt.return_value = MagicMock()
    # Return invalid headers that aren't 'JWT'
    mock_decode_complete.return_value = {
        'payload': CMS_ALIGNED_NETWORKS_PAYLOAD,
        'header': {'typ': header},
    }

    with pytest.raises(InvalidRequestError):
        validator._decode_and_validate_token('token', 'test_iss', mock_jwks_client)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class',
    [
        (CMSAlignedNetworksValidator),
        (AsymmetricAuthValidator),
    ],
)
@override_switch('client_credentials_validation', active=True)
@override_switch('asymmetric_auth_validation', active=True)
@patch('jwt.decode_complete')
def test_decode_and_validate_token_expired(
    mock_decode_complete,
    validator_class,
):
    """Test _decode_and_validate_token fails with expired token"""

    validator = validator_class()
    mock_jwks_client = MagicMock()
    mock_jwks_client.get_signing_key_from_jwt.return_value = MagicMock()
    # Make expiration time 6 minutes in the past to simulate an expired token scenario
    # Don't modify the original CMS_ALIGNED_NETWORKS_PAYLOAD directly
    test_payload = CMS_ALIGNED_NETWORKS_PAYLOAD.copy()
    test_payload['exp'] = datetime.datetime.now(timezone.utc).timestamp() + 360
    mock_decode_complete.return_value = {
        'payload': test_payload,
        'header': {'typ': 'JWT'},
    }

    with pytest.raises(InvalidRequestError):
        validator._decode_and_validate_token('token', 'test_iss', mock_jwks_client)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, jti',
    [
        (CMSAlignedNetworksValidator, 'can_cache_replay'),
    ],
)
@override_switch('client_credentials_validation', active=True)
@patch('jwt.decode_complete')
def test_validate_ial_jwt_success(
    mock_decode_complete,
    validator_class,
    jti,
):
    """Test _validate_ial_jwt succeeds with basic validation."""

    with freeze_time() as frozen_time:
        mock_jwks_client = MagicMock()
        mock_jwks_client.get_signing_key_from_jwt.return_value = MagicMock()
        # Don't modify the original VALID_IAL_JWT_PAYLOAD directly
        test_payload = VALID_IAL_JWT_PAYLOAD.copy()
        test_payload['jti'] = jti
        mock_decode_complete.return_value = {
            'payload': test_payload,
            'header': {'typ': 'JWT'},
        }

        # Call succeeds
        validator = validator_class()
        result = validator._validate_ial_jwt('token', mock_jwks_client)
        assert result == test_payload

        # Assert cache has the key we'd expect and that the result is what we'd expect
        cache_key = f'{test_payload.get("iss")}-{test_payload.get("jti")}'
        assert cache.get(cache_key) == 'sentinel'

        # Advance time by 300 seconds and assert cache no longer has key
        frozen_time.tick(delta=datetime.timedelta(seconds=300))
        assert cache.get(cache_key) is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, jti',
    [
        (CMSAlignedNetworksValidator, 'can_cache_replay'),
    ],
)
@override_switch('client_credentials_validation', active=True)
@override_switch('asymmetric_auth_validation', active=True)
@patch('jwt.decode_complete')
def test_validate_ial_jwt_cache_replay_unsuccessful(
    mock_decode_complete,
    validator_class,
    jti,
):
    """Test _validate_ial_jwt fails on second cache hit with same iss/jti combo"""

    validator = validator_class()
    mock_jwks_client = MagicMock()
    mock_jwks_client.get_signing_key_from_jwt.return_value = MagicMock()
    # Don't modify the original VALID_IAL_JWT_PAYLOAD directly
    test_payload = VALID_IAL_JWT_PAYLOAD.copy()
    test_payload['jti'] = jti
    mock_decode_complete.return_value = {
        'payload': test_payload,
        'header': {'typ': 'JWT'},
    }

    result = validator._validate_ial_jwt('token', mock_jwks_client)
    assert result == test_payload

    # Assert cache has the key we'd expect and that the result is what we'd expect
    cache_key = f'{test_payload.get("iss")}-{test_payload.get("jti")}'
    assert cache.get(cache_key) == 'sentinel'

    # Second call with same jti/iss fails
    with pytest.raises(InvalidRequestError):
        validator._validate_ial_jwt('token', mock_jwks_client)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, header',
    [
        (CMSAlignedNetworksValidator, 'invalid-typ'),
    ],
)
@override_switch('client_credentials_validation', active=True)
@override_switch('asymmetric_auth_validation', active=True)
@patch('jwt.decode_complete')
def test_validate_ial_jwt_invalid_header(
    mock_decode_complete,
    validator_class,
    header,
):
    """Test _validate_ial_jwt fails with invalid typ in header"""

    validator = validator_class()
    mock_jwks_client = MagicMock()
    mock_jwks_client.get_signing_key_from_jwt.return_value = MagicMock()
    # Return invalid headers that aren't 'JWT'
    mock_decode_complete.return_value = {
        'payload': VALID_IAL_JWT_PAYLOAD,
        'header': {'typ': header},
    }

    with pytest.raises(InvalidRequestError):
        validator._validate_ial_jwt('token', mock_jwks_client)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, claim, value',
    [
        (CMSAlignedNetworksValidator, 'identity_assurance_level', 1),
        (CMSAlignedNetworksValidator, 'birthdate', 'cdjcdhbfdf'),
    ],
)
@override_switch('client_credentials_validation', active=True)
@override_switch('asymmetric_auth_validation', active=True)
@patch('jwt.decode_complete')
def test_validate_ial_jwt_invalid_request(
    mock_decode_complete,
    validator_class,
    claim,
    value,
):
    """Test _validate_ial_jwt fails with invalid request"""

    validator = validator_class()
    mock_jwks_client = MagicMock()
    mock_jwks_client.get_signing_key_from_jwt.return_value = MagicMock()
    # Don't modify the original VALID_IAL_JWT_PAYLOAD directly
    test_payload = VALID_IAL_JWT_PAYLOAD.copy()
    test_payload[claim] = value
    mock_decode_complete.return_value = {
        'payload': test_payload,
        'header': {'typ': 'JWT'},
    }

    with pytest.raises(InvalidRequestError):
        validator._validate_ial_jwt('token', mock_jwks_client)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, target_env, parameter, expected_result',
    [
        (CMSAlignedNetworksValidator, 'prod', CLEAR_HIGHER_ISS, True),
        (CMSAlignedNetworksValidator, 'prod', CLEAR_LOWER_ISS, True),
        (CMSAlignedNetworksValidator, 'prod', IDME_HIGHER_ISS, True),
        (CMSAlignedNetworksValidator, 'prod', IDME_LOWER_ISS, False),
        (CMSAlignedNetworksValidator, 'impl', IDME_HIGHER_ISS, False),
        (CMSAlignedNetworksValidator, 'impl', IDME_LOWER_ISS, True),
        (CMSAlignedNetworksValidator, 'test', IDME_HIGHER_ISS, False),
        (CMSAlignedNetworksValidator, 'test', IDME_LOWER_ISS, True),
        (CMSAlignedNetworksValidator, 'local', IDME_HIGHER_ISS, False),
        (CMSAlignedNetworksValidator, 'local', IDME_LOWER_ISS, True),
    ],
)
@override_switch('client_credentials_validation', active=True)
def test_validate_environment_for_id_token(validator_class, target_env, parameter, expected_result) -> None:
    """Confirm that, given a specific environment and an issuer URL, the
    _validate_idme_url_for_id_token_and_environment will correctly return True or False
    """
    validator = validator_class()
    os.environ['TARGET_ENV'] = target_env
    result = validator._validate_idme_url_for_id_token_and_environment(parameter)
    assert result == expected_result


@pytest.mark.django_db
@pytest.mark.parametrize(
    'payload, expected_output, should_raise',
    [
        (EXTENSIONS_PAYLOAD, 'alksjdlksajdlskajdskladsksdalkdsakldaskldaskljadsj', False),
        ({}, None, True),
        (
            {
                'extensions': {
                    'cms_smart': {
                        'version': 'INVALID',
                        'purpose_of_use': 'PATRQT',
                        'id_token': 'alksjdlksajdlskajdskladsksdalkdsakldaskldaskljadsj',
                    }
                }
            },
            None,
            True,
        ),
        (
            {
                'extensions': {
                    'cms_smart': {
                        'version': '1',
                        'purpose_of_use': 'INVALID',
                        'id_token': 'alksjdlksajdlskajdskladsksdalkdsakldaskldaskljadsj',
                    }
                }
            },
            None,
            True,
        ),
    ],
)
@override_switch('client_credentials_validation', active=True)
def test_validate_smart_extension(payload, expected_output, should_raise):
    """Test _validate_smart_extension for correct behavior"""
    validator = CMSAlignedNetworksValidator()
    if should_raise:
        with pytest.raises(InvalidRequestError):
            validator._validate_smart_extension(payload)
    else:
        result = validator._validate_smart_extension(payload)
        assert result == expected_output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'iss, expected_result, should_raise, environment',
    [
        (CLEAR_HIGHER_ISS, settings.CLEAR_HIGHER_JWKS_URL, False, 'prod'),
        (CLEAR_HIGHER_ISS, settings.CLEAR_HIGHER_JWKS_URL, False, 'local'),
        (CLEAR_HIGHER_ISS, settings.CLEAR_HIGHER_JWKS_URL, False, 'test'),
        (CLEAR_HIGHER_ISS, settings.CLEAR_HIGHER_JWKS_URL, False, 'sbx'),
        (IDME_HIGHER_ISS, settings.IDME_HIGHER_JWKS_URL, False, 'prod'),
        (IDME_LOWER_ISS, settings.IDME_LOWER_JWKS_URL, False, 'local'),
        (IDME_LOWER_ISS, settings.IDME_LOWER_JWKS_URL, False, 'test'),
        (IDME_LOWER_ISS, settings.IDME_LOWER_JWKS_URL, False, 'sbx'),
        ('INVALID_ISS', None, True, 'local'),
        ('INVALID_ISS', None, True, 'test'),
        ('INVALID_ISS', None, True, 'sbx'),
        ('INVALID_ISS', None, True, 'prod'),
    ],
)
@override_switch('client_credentials_validation', active=True)
def test_get_csp_jwks_url(iss, expected_result, should_raise, environment, settings):
    """Test _get_csp_jwks_url for correct behavior"""
    validator = CMSAlignedNetworksValidator()
    settings.TARGET_ENV = environment
    token = jwt.encode({'iss': iss}, 'secret', algorithm='HS256')
    if should_raise:
        with pytest.raises(InvalidRequestError):
            validator._get_csp_jwks_url(token)
    else:
        result = validator._get_csp_jwks_url(token)
        assert result == expected_result


@pytest.mark.parametrize(
    'payload, mock_normalized_address, expected_output',
    [
        (
            {
                'family_name': 'Smith',
                'given_name': 'John',
                'phone_number': '+15555555555',
                'phone_number_verified': True,
                'email': 'john@example.com',
                'gender': 'MALE',
                'birthdate': '1990-01-01',
                'address': {
                    'street_address': '123 Main St',
                    'locality': 'Baltimore',
                    'region': 'MD',
                    'postal_code': '21201',
                    'country': 'US',
                },
                'ssn_itin_short': '1234',
            },
            '123 Main St, Baltimore, MD, 21201',
            {
                'id': 'IDIMatchInputParameters',
                'meta': {
                    'profile': [
                        'http://hl7.org/fhir/us/identity-matching/StructureDefinition/idi-match-input-parameters',
                    ],
                },
                'parameter': [
                    {
                        'name': 'IDIPatient',
                        'resource': {
                            'resourceType': 'Patient',
                            'meta': {
                                'profile': [
                                    'http://hl7.org/fhir/us/identity-matching/StructureDefinition/IDI-Patient',
                                ],
                            },
                            'name': [{'use': 'official', 'family': 'Smith', 'given': ['John']}],
                            'gender': 'male',
                            'birthDate': '1990-01-01',
                            'telecom': [
                                {'system': 'phone', 'value': '+15555555555', 'use': 'mobile', 'rank': 1},
                                {'system': 'email', 'value': 'john@example.com', 'use': 'home', 'rank': 2},
                            ],
                            'address': [
                                {
                                    'use': 'home',
                                    'type': 'both',
                                    'text': '123 Main St, Baltimore, MD, 21201',
                                    'line': ['123 Main St, Baltimore, MD, 21201'],
                                    'city': 'Baltimore',
                                    'state': 'MD',
                                    'postalCode': '21201',
                                    'country': 'US',
                                }
                            ],
                            'identifier': [
                                {
                                    'use': 'official',
                                    'system': 'http://hl7.org/fhir/sid/us-ssn',
                                    'type': {
                                        'coding': [
                                            {
                                                'code': 'SS',
                                                'display': 'Social Security Number',
                                                'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                                            },
                                        ],
                                    },
                                    'value': '1234',
                                }
                            ],
                        },
                    }
                ],
                'resourceType': 'Parameters',
            },
        ),
        (
            {
                'family_name': 'Doe',
                'given_name': 'Jane',
                'phone_number': '+15555555555',
                'phone_number_verified': False,  # set to false for testing
                'email': 'jane@example.com',
            },
            None,
            {
                'id': 'IDIMatchInputParameters',
                'meta': {
                    'profile': [
                        'http://hl7.org/fhir/us/identity-matching/StructureDefinition/idi-match-input-parameters',
                    ],
                },
                'parameter': [
                    {
                        'name': 'IDIPatient',
                        'resource': {
                            'address': [],
                            'gender': 'unknown',
                            'identifier': [],
                            'meta': {
                                'profile': [
                                    'http://hl7.org/fhir/us/identity-matching/StructureDefinition/IDI-Patient',
                                ],
                            },
                            'name': [
                                {
                                    'family': 'Doe',
                                    'given': [
                                        'Jane',
                                    ],
                                    'use': 'official',
                                },
                            ],
                            'resourceType': 'Patient',
                            'telecom': [
                                {
                                    'rank': 2,
                                    'system': 'email',
                                    'use': 'home',
                                    'value': 'jane@example.com',
                                },
                            ],
                        },
                    },
                ],
                'resourceType': 'Parameters',
            },
        ),
        (
            {
                'family_name': 'Doe',
                'given_name': 'Sam',
                'SSN': '000-11-6789',  # Short version of SSN missing, slice last 4 digits
            },
            None,
            {
                'id': 'IDIMatchInputParameters',
                'meta': {
                    'profile': [
                        'http://hl7.org/fhir/us/identity-matching/StructureDefinition/idi-match-input-parameters',
                    ],
                },
                'parameter': [
                    {
                        'name': 'IDIPatient',
                        'resource': {
                            'address': [],
                            'gender': 'unknown',
                            'identifier': [
                                {
                                    'system': 'http://hl7.org/fhir/sid/us-ssn',
                                    'type': {
                                        'coding': [
                                            {
                                                'code': 'SS',
                                                'display': 'Social Security Number',
                                                'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                                            },
                                        ],
                                    },
                                    'use': 'official',
                                    'value': '6789',
                                },
                            ],
                            'meta': {
                                'profile': [
                                    'http://hl7.org/fhir/us/identity-matching/StructureDefinition/IDI-Patient',
                                ],
                            },
                            'name': [
                                {
                                    'family': 'Doe',
                                    'given': [
                                        'Sam',
                                    ],
                                    'use': 'official',
                                },
                            ],
                            'resourceType': 'Patient',
                            'telecom': [],
                        },
                    },
                ],
                'resourceType': 'Parameters',
            },
        ),
        (
            {
                'family_name': 'Doe',
                'given_name': 'Sam',
                # Historical address information for the patient gets parsed into the FHIR Patient resource as old addresses
                'historical_address': [
                    {
                        'street_address': '456 Old Rd',
                        'locality': 'Boston',
                        'region': 'MA',
                        'postal_code': '02108',
                        'country': 'US',
                    }
                ],
            },
            '456 Old Rd, Boston, MA, 02108',
            {
                'resourceType': 'Parameters',
                'id': 'IDIMatchInputParameters',
                'meta': {
                    'profile': [
                        'http://hl7.org/fhir/us/identity-matching/StructureDefinition/idi-match-input-parameters'
                    ]
                },
                'parameter': [
                    {
                        'name': 'IDIPatient',
                        'resource': {
                            'resourceType': 'Patient',
                            'meta': {
                                'profile': ['http://hl7.org/fhir/us/identity-matching/StructureDefinition/IDI-Patient']
                            },
                            'identifier': [],
                            'name': [{'use': 'official', 'family': 'Doe', 'given': ['Sam']}],
                            'telecom': [],
                            'gender': 'unknown',
                            'address': [
                                {
                                    'use': 'old',
                                    'type': 'both',
                                    'text': '456 Old Rd, Boston, MA, 02108',
                                    'line': ['456 Old Rd, Boston, MA, 02108'],
                                    'city': 'Boston',
                                    'state': 'MA',
                                    'postalCode': '02108',
                                    'country': 'US',
                                }
                            ],
                        },
                    }
                ],
            },
        ),
    ],
)
@patch('apps.dot_ext.validators.normalize_address')
def test_parse_ial_into_parameter(mock_normalize, payload, mock_normalized_address, expected_output):
    """Test _parse_into_parameter for correct behavior"""
    validator = CMSAlignedNetworksValidator()
    mock_normalize.return_value = mock_normalized_address
    result = validator._parse_ial_into_parameter(payload)
    assert result == expected_output
