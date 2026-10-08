import datetime
import json
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


def create_mock_pyjwk(kid: str, kty: str, fake_key: str) -> MagicMock:
    """Helper factory to create mock objects that mirror pyjwt.PyJWK instances."""
    mock_jwk_obj = MagicMock()
    mock_jwk_obj.key_id = kid
    mock_jwk_obj.key_type = kty
    mock_jwk_obj.key = fake_key
    return mock_jwk_obj


def load_fhir_json(filename):
    """Helper function to load JSON test data from the test_data directory."""
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, 'test_data', filename)
    with open(file_path, 'r') as f:
        return json.load(f)


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


@pytest.mark.django_db
@pytest.mark.parametrize(
    'jku, header, should_raise',
    [
        # Case for testing the 'jku' header field validation matches the expected JWKS URL
        (
            'https://example.com/jwks.json',
            {'typ': 'JWT', 'kid': 'some-kid', 'jku': 'https://example.com/jwks.json'},
            False,
        ),
        # Case where the 'jku' header is missing
        ('https://example.com/jwks.json', {'typ': 'JWT', 'kid': 'some-kid'}, False),
        # Case where the 'jku' header does not match the expected JWKS URL
        (
            'different-jwks_url',
            {'typ': 'JWT', 'kid': 'some-kid', 'jku': 'https://example.com/jwks.json'},
            True,
        ),
    ],
)
@override_switch('asymmetric_auth_validation', active=True)
def test_validate_and_get_jwks_uri(jku, header, should_raise):
    """Test the validation of the 'jku' header field for successful and unsuccessful cases."""
    validator = AsymmetricAuthValidator()
    token = jwt.encode(ASYMMETRIC_AUTH_PAYLOAD.copy(), 'secret', algorithm='HS256', headers=header)

    if should_raise:
        with pytest.raises(InvalidRequestError):
            validator._validate_and_get_jwks_uri(token, jku)
    else:
        response = validator._validate_and_get_jwks_uri(token, jku)
        assert response == jku


@pytest.mark.django_db
@pytest.mark.parametrize(
    'mock_payload, claim_key, time_window, should_raise',
    [
        # Case where the 'auth_time' field is a string, which should raise an error
        (
            {'auth_time': "I'm a string"},
            'auth_time',
            300,
            True,
        ),
        # Case where the 'iat' field is a string, which should raise an error
        (
            {'iat': "I'm a string"},
            'iat',
            300,
            True,
        ),
        # Case where the 'auth_time' field is in the future, which should raise an error
        (
            {'auth_time': datetime.datetime.now(timezone.utc).timestamp() + 60},
            'auth_time',
            300,
            True,
        ),
        # Case where the 'iat' field is in the future, which should raise an error
        (
            {'iat': datetime.datetime.now(timezone.utc).timestamp() + 60},
            'iat',
            300,
            True,
        ),
        # Case where the 'auth_time' field is too far in the past, which should raise an error
        (
            {'auth_time': datetime.datetime.now(timezone.utc).timestamp() - 301},
            'auth_time',
            300,
            True,
        ),
        # Case where the 'iat' field is too far in the past, which should raise an error
        (
            {'iat': datetime.datetime.now(timezone.utc).timestamp() - 301},
            'iat',
            300,
            True,
        ),
        # Case where the 'auth_time' field is within the acceptable time window, which should not raise an error
        (
            {'auth_time': datetime.datetime.now(timezone.utc).timestamp() - 180},
            'auth_time',
            300,
            False,
        ),
        # Case where the 'iat' field is within the acceptable time window, which should not raise an error
        (
            {'iat': datetime.datetime.now(timezone.utc).timestamp() - 180},
            'iat',
            300,
            False,
        ),
    ],
)
def test_validate_time_comparison(mock_payload, claim_key, time_window, should_raise):
    """Test the successful and unsuccessful _validate_time_comparison cases."""
    validator = CMSAlignedNetworksValidator()
    if should_raise:
        with pytest.raises(InvalidRequestError):
            validator._validate_time_comparison(mock_payload, claim_key, time_window)
    else:
        response = validator._validate_time_comparison(mock_payload, claim_key, time_window)
        assert response is True


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, jti',
    [(CMSAlignedNetworksValidator, 'can_cache_replay'), (AsymmetricAuthValidator, 'asym_auth_cache_replay')],
)
@override_switch('client_credentials_validation', active=True)
@override_switch('asymmetric_auth_validation', active=True)
@patch('apps.dot_ext.validators.CMSAlignedNetworksValidator._get_signing_key')
@patch('apps.dot_ext.validators.AsymmetricAuthValidator._get_signing_key')
@patch('jwt.decode_complete')
def test_validate_and_decode_token_cache_successful(
    mock_decode_complete,
    mock_asym_auth_get_signing_key,
    mock_cms_get_signing_key,
    validator_class,
    jti,
):
    """Test correct cache behavior for _validate_and_decode_token"""
    validator = validator_class()
    mock_asym_auth_get_signing_key.return_value = MagicMock()
    mock_cms_get_signing_key.return_value = MagicMock()
    with freeze_time() as frozen_time:
        # Don't modify the original CMS_ALIGNED_NETWORKS_PAYLOAD directly
        test_payload = CMS_ALIGNED_NETWORKS_PAYLOAD.copy()
        test_payload['jti'] = jti
        mock_decode_complete.return_value = {
            'payload': test_payload,
            'header': {'typ': 'JWT'},
        }

        result = validator._decode_and_validate_token('token', 'test_iss', 'jwks_uri')
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
@patch('apps.dot_ext.validators.CMSAlignedNetworksValidator._get_signing_key')
@patch('apps.dot_ext.validators.AsymmetricAuthValidator._get_signing_key')
@patch('jwt.decode_complete')
def test_decode_and_validate_token_cache_replay_unsuccessful(
    mock_decode_complete,
    mock_asym_auth_get_signing_key,
    mock_cms_get_signing_key,
    validator_class,
    jti,
):
    """Test _decode_and_validate_token fails on second cache hit with same iss/jti combo"""
    validator = validator_class()
    mock_asym_auth_get_signing_key.return_value = MagicMock()
    mock_cms_get_signing_key.return_value = MagicMock()
    # Don't modify the original CMS_ALIGNED_NETWORKS_PAYLOAD directly
    test_payload = CMS_ALIGNED_NETWORKS_PAYLOAD.copy()
    test_payload['jti'] = jti
    mock_decode_complete.return_value = {
        'payload': test_payload,
        'header': {'typ': 'JWT'},
    }

    result = validator._decode_and_validate_token('token', 'test_iss', 'jwks_uri')
    assert result == test_payload

    # Assert cache has the key we'd expect and that the result is what we'd expect
    cache_key = f'{test_payload.get("iss")}-{test_payload.get("jti")}'
    assert cache.get(cache_key) == 'sentinel'

    # Second call with same jti/iss fails
    with pytest.raises(InvalidRequestError):
        validator._decode_and_validate_token('token', 'test_iss', 'jwks_uri')


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
@patch('apps.dot_ext.validators.CMSAlignedNetworksValidator._get_signing_key')
@patch('apps.dot_ext.validators.AsymmetricAuthValidator._get_signing_key')
@patch('jwt.decode_complete')
def test_decode_and_validate_token_invalid_header(
    mock_decode_complete,
    mock_asym_auth_get_signing_key,
    mock_cms_get_signing_key,
    validator_class,
    header,
):
    """Test _decode_and_validate_token fails with invalid typ in header"""

    validator = validator_class()
    mock_asym_auth_get_signing_key.return_value = MagicMock()
    mock_cms_get_signing_key.return_value = MagicMock()
    # Return invalid headers that aren't 'JWT'
    mock_decode_complete.return_value = {
        'payload': CMS_ALIGNED_NETWORKS_PAYLOAD,
        'header': {'typ': header},
    }

    with pytest.raises(InvalidRequestError):
        validator._decode_and_validate_token('token', 'test_iss', 'jwks_uri')


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
@patch('apps.dot_ext.validators.CMSAlignedNetworksValidator._get_signing_key')
@patch('apps.dot_ext.validators.AsymmetricAuthValidator._get_signing_key')
@patch('jwt.decode_complete')
def test_decode_and_validate_token_expired(
    mock_decode_complete,
    mock_asym_auth_get_signing_key,
    mock_cms_get_signing_key,
    validator_class,
):
    """Test _decode_and_validate_token fails with expired token"""
    validator = validator_class()
    mock_asym_auth_get_signing_key.return_value = MagicMock()
    mock_cms_get_signing_key.return_value = MagicMock()
    # Make expiration time 6 minutes in the past to simulate an expired token scenario
    # Don't modify the original CMS_ALIGNED_NETWORKS_PAYLOAD directly
    test_payload = CMS_ALIGNED_NETWORKS_PAYLOAD.copy()
    test_payload['exp'] = datetime.datetime.now(timezone.utc).timestamp() + 360
    mock_decode_complete.return_value = {
        'payload': test_payload,
        'header': {'typ': 'JWT'},
    }

    with pytest.raises(InvalidRequestError):
        validator._decode_and_validate_token('token', 'test_iss', 'jwks_uri')


@pytest.mark.django_db
@override_switch('client_credentials_validation', active=True)
@patch('apps.dot_ext.validators.CMSAlignedNetworksValidator._get_signing_key')
@patch('jwt.decode_complete')
def test_validate_ial_jwt_success(
    mock_decode_complete,
    mock_cms_get_signing_key,
):
    """Test _validate_ial_jwt succeeds with basic validation."""
    mock_cms_get_signing_key.return_value = MagicMock()
    with freeze_time() as frozen_time:
        # Don't modify the original VALID_IAL_JWT_PAYLOAD directly
        test_payload = VALID_IAL_JWT_PAYLOAD.copy()
        test_payload['jti'] = 'can_cache_replay'
        mock_decode_complete.return_value = {
            'payload': test_payload,
            'header': {'typ': 'JWT'},
        }

        validator = CMSAlignedNetworksValidator()
        result = validator._validate_ial_jwt('token', 'jwks_uri')
        assert result == test_payload

        # Assert cache has the key we'd expect and that the result is what we'd expect
        cache_key = f'{test_payload.get("iss")}-{test_payload.get("jti")}'
        assert cache.get(cache_key) == 'sentinel'

        # Advance time by 300 seconds and assert cache no longer has key
        frozen_time.tick(delta=datetime.timedelta(seconds=300))
        assert cache.get(cache_key) is None


@pytest.mark.django_db
@override_switch('client_credentials_validation', active=True)
@override_switch('asymmetric_auth_validation', active=True)
@patch('apps.dot_ext.validators.CMSAlignedNetworksValidator._get_signing_key')
@patch('jwt.decode_complete')
def test_validate_ial_jwt_cache_replay_unsuccessful(
    mock_decode_complete,
    mock_cms_get_signing_key,
):
    """Test _validate_ial_jwt fails on second cache hit with same iss/jti combo"""
    validator = CMSAlignedNetworksValidator()
    mock_cms_get_signing_key.return_value = MagicMock()
    # Don't modify the original VALID_IAL_JWT_PAYLOAD directly
    test_payload = VALID_IAL_JWT_PAYLOAD.copy()
    test_payload['jti'] = 'can_cache_replay'
    mock_decode_complete.return_value = {
        'payload': test_payload,
        'header': {'typ': 'JWT'},
    }

    result = validator._validate_ial_jwt('token', 'jwks_uri')
    assert result == test_payload

    # Assert cache has the key we'd expect and that the result is what we'd expect
    cache_key = f'{test_payload.get("iss")}-{test_payload.get("jti")}'
    assert cache.get(cache_key) == 'sentinel'

    # Second call with same jti/iss fails
    with pytest.raises(InvalidRequestError):
        validator._validate_ial_jwt('token', 'jwks_uri')


@pytest.mark.django_db
@override_switch('client_credentials_validation', active=True)
@override_switch('asymmetric_auth_validation', active=True)
@patch('apps.dot_ext.validators.CMSAlignedNetworksValidator._get_signing_key')
@patch('jwt.decode_complete')
def test_validate_ial_jwt_invalid_header(
    mock_decode_complete,
    mock_cms_get_signing_key,
):
    """Test _validate_ial_jwt fails with invalid typ in header"""
    validator = CMSAlignedNetworksValidator()
    mock_cms_get_signing_key.return_value = MagicMock()
    # Return invalid headers that aren't 'JWT'
    mock_decode_complete.return_value = {
        'payload': VALID_IAL_JWT_PAYLOAD,
        'header': {'typ': 'random_header'},
    }

    with pytest.raises(InvalidRequestError):
        validator._validate_ial_jwt('token', 'jwks_uri')


@pytest.mark.django_db
@pytest.mark.parametrize(
    'claim, value',
    [
        ('identity_assurance_level', 1),
        ('birthdate', 'cdjcdhbfdf'),
    ],
)
@override_switch('client_credentials_validation', active=True)
@override_switch('asymmetric_auth_validation', active=True)
@patch('apps.dot_ext.validators.CMSAlignedNetworksValidator._get_signing_key')
@patch('jwt.decode_complete')
def test_validate_ial_jwt_invalid_request(
    mock_decode_complete,
    mock_cms_get_signing_key,
    claim,
    value,
):
    """Test _validate_ial_jwt fails with invalid identity assurance level or birthdate"""
    validator = CMSAlignedNetworksValidator()
    mock_cms_get_signing_key.return_value = MagicMock()
    # Don't modify the original VALID_IAL_JWT_PAYLOAD directly
    test_payload = VALID_IAL_JWT_PAYLOAD.copy()
    test_payload[claim] = value
    mock_decode_complete.return_value = {
        'payload': test_payload,
        'header': {'typ': 'JWT'},
    }

    with pytest.raises(InvalidRequestError):
        validator._validate_ial_jwt('token', 'jwks_uri')


@pytest.mark.django_db
@pytest.mark.parametrize(
    'target_env, parameter, expected_result',
    [
        ('prod', CLEAR_HIGHER_ISS, True),
        ('prod', CLEAR_LOWER_ISS, True),
        ('prod', IDME_HIGHER_ISS, True),
        ('prod', IDME_LOWER_ISS, False),
        ('impl', IDME_HIGHER_ISS, False),
        ('impl', IDME_LOWER_ISS, True),
        ('test', IDME_HIGHER_ISS, False),
        ('test', IDME_LOWER_ISS, True),
        ('local', IDME_HIGHER_ISS, False),
        ('local', IDME_LOWER_ISS, True),
    ],
)
@override_switch('client_credentials_validation', active=True)
def test_validate_environment_for_id_token(target_env, parameter, expected_result) -> None:
    """Confirm that, given a specific environment and an issuer URL, the
    _validate_idme_url_for_id_token_and_environment will correctly return True or False
    """
    validator = CMSAlignedNetworksValidator()
    os.environ['TARGET_ENV'] = target_env
    result = validator._validate_idme_url_for_id_token_and_environment(parameter)
    assert result == expected_result


@pytest.mark.django_db
@pytest.mark.parametrize(
    'payload, expected_output, should_raise',
    [
        # Valid payload with correct extensions should return the id_token without raising an error
        (EXTENSIONS_PAYLOAD, 'alksjdlksajdlskajdskladsksdalkdsakldaskldaskljadsj', False),
        # Invalid payload without extensions should raise an error
        ({}, None, True),
        # Invalid payload with incorrect version should raise an error
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
        # Invalid payload with incorrect purpose_of_use should raise an error
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
    'payload, mock_normalized_address, json_file_response',
    [
        (
            # Happy path test case for a valid patient payload
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
            'happy_path_response.json',
        ),
        # Test case for a patient with an unverified phone number
        (
            {
                'family_name': 'Doe',
                'given_name': 'Jane',
                'phone_number': '+15555555555',
                'phone_number_verified': False,
                'email': 'jane@example.com',
            },
            None,
            'phone_unverified_response.json',
        ),
        # Test case for a patient with an SSN that needs slicing
        (
            {
                'family_name': 'Doe',
                'given_name': 'Sam',
                'SSN': '000-11-6789',
            },
            None,
            'slice_ssn_response.json',
        ),
        # Test case for a patient with historical address information
        (
            {
                'family_name': 'Doe',
                'given_name': 'Sam',
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
            'historical_address_response.json',
        ),
    ],
)
@patch('apps.dot_ext.validators.normalize_address')
def test_parse_ial_into_parameter(mock_normalize, payload, mock_normalized_address, json_file_response):
    """Test _parse_into_parameter for correct behavior"""
    validator = CMSAlignedNetworksValidator()
    mock_normalize.return_value = mock_normalized_address
    expected_output = load_fhir_json(json_file_response)
    result = validator._parse_ial_into_parameter(payload)
    assert result == expected_output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'validator_class, token, jwks_uri, mocked_keys, token_kid, token_alg, should_raise, expected_key',
    [
        # Successful retrieval of signing key with matching kid in JWKS and correct algorithm
        (
            CMSAlignedNetworksValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'RSA', 'real-rsa-key'),
                create_mock_pyjwk('different-kid', 'RSA', 'ignored-key'),
            ],
            'kid-v1',
            'RS256',
            False,
            'real-rsa-key',
        ),
        # Successful retrieval of signing key with matching kid in JWKS and correct algorithm (switch algorithms)
        (
            CMSAlignedNetworksValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'EC', 'real-es-key'),
                create_mock_pyjwk('different-kid', 'EC', 'ignored-key'),
            ],
            'kid-v1',
            'ES384',
            False,
            'real-es-key',
        ),
        # Case where the 'kid' in the token does not match any key in the JWKS and thus should raise an error
        # with 0 matching keys in the JWKS
        (
            CMSAlignedNetworksValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'RSA', 'real-rsa-key'),
                create_mock_pyjwk('different-kid', 'RSA', 'ignored-key'),
            ],
            'non-existent-kid',
            'RS256',
            True,
            None,
        ),
        # Case where the 'alg' in the token does not match the key's algorithm and thus should raise an error
        # with 0 matching keys in the JWKS
        (
            CMSAlignedNetworksValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'RSA', 'real-rsa-key'),
                create_mock_pyjwk('different-kid', 'RSA', 'ignored-key'),
            ],
            'kid-v1',
            'ES256',
            True,
            None,
        ),
        # Case where the 'alg' in the token does not match the key's algorithm and thus should raise an error
        # with 0 matching keys in the JWKS (switches algorithms)
        (
            CMSAlignedNetworksValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'EC', 'real-es-key'),
                create_mock_pyjwk('different-kid', 'EC', 'ignored-key'),
            ],
            'kid-v1',
            'RSA256',
            True,
            None,
        ),
        # Case where both the 'kid' and 'alg' in the token do not match any key in the JWKS and
        # thus should raise an error with 0 matching keys in the JWKS
        (
            CMSAlignedNetworksValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'RSA', 'real-rsa-key'),
                create_mock_pyjwk('different-kid', 'RSA', 'ignored-key'),
            ],
            'non-existent-kid',
            'ES256',
            True,
            None,
        ),
        # Case where there are multiple matches
        (
            CMSAlignedNetworksValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'EC', 'real-es-key'),
                create_mock_pyjwk('kid-v1', 'EC', 'real-es-key'),
            ],
            'kid-v1',
            'ES384',
            True,
            None,
        ),
        # Case where there are multiple matches (switch alogrithms)
        (
            CMSAlignedNetworksValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'RSA', 'real-rsa-key'),
                create_mock_pyjwk('kid-v1', 'RSA', 'real-rsa-key'),
            ],
            'kid-v1',
            'RS256',
            True,
            None,
        ),
        # Successful retrieval of signing key with matching kid in JWKS and correct algorithm
        (
            AsymmetricAuthValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'RSA', 'real-rsa-key'),
                create_mock_pyjwk('different-kid', 'RSA', 'ignored-key'),
            ],
            'kid-v1',
            'RS256',
            False,
            'real-rsa-key',
        ),
        # Successful retrieval of signing key with matching kid in JWKS and correct algorithm (switch algorithms)
        (
            AsymmetricAuthValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'EC', 'real-es-key'),
                create_mock_pyjwk('different-kid', 'EC', 'ignored-key'),
            ],
            'kid-v1',
            'ES384',
            False,
            'real-es-key',
        ),
        # Case where the 'kid' in the token does not match any key in the JWKS and thus should raise an error
        # with 0 matching keys in the JWKS
        (
            AsymmetricAuthValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'RSA', 'real-rsa-key'),
                create_mock_pyjwk('different-kid', 'RSA', 'ignored-key'),
            ],
            'non-existent-kid',
            'RS256',
            True,
            None,
        ),
        # Case where the 'alg' in the token does not match the key's algorithm and thus should raise an error
        # with 0 matching keys in the JWKS
        (
            AsymmetricAuthValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'RSA', 'real-rsa-key'),
                create_mock_pyjwk('different-kid', 'RSA', 'ignored-key'),
            ],
            'kid-v1',
            'ES256',
            True,
            None,
        ),
        # Case where the 'alg' in the token does not match the key's algorithm and thus should raise an error
        # with 0 matching keys in the JWKS (switches algorithms)
        (
            AsymmetricAuthValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'EC', 'real-es-key'),
                create_mock_pyjwk('different-kid', 'EC', 'ignored-key'),
            ],
            'kid-v1',
            'RSA256',
            True,
            None,
        ),
        # Case where both the 'kid' and 'alg' in the token do not match any key in the JWKS and
        # thus should raise an error with 0 matching keys in the JWKS
        (
            AsymmetricAuthValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'RSA', 'real-rsa-key'),
                create_mock_pyjwk('different-kid', 'RSA', 'ignored-key'),
            ],
            'non-existent-kid',
            'ES256',
            True,
            None,
        ),
        # Case where there are multiple matches
        (
            AsymmetricAuthValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'EC', 'real-es-key'),
                create_mock_pyjwk('kid-v1', 'EC', 'real-es-key'),
            ],
            'kid-v1',
            'ES384',
            True,
            None,
        ),
        # Case where there are multiple matches (switch alogrithms)
        (
            AsymmetricAuthValidator,
            'dummy_token',
            'https://example.com/.well-known/jwks.json',
            [
                create_mock_pyjwk('kid-v1', 'RSA', 'real-rsa-key'),
                create_mock_pyjwk('kid-v1', 'RSA', 'real-rsa-key'),
            ],
            'kid-v1',
            'RS256',
            True,
            None,
        ),
    ],
)
@patch('jwt.get_unverified_header')
@patch('jwt.PyJWKClient')
def test_get_signing_key(
    mock_pyjwk_client,
    mock_get_unverified_header,
    validator_class,
    token,
    jwks_uri,
    mocked_keys,
    token_kid,
    token_alg,
    should_raise,
    expected_key,
):
    """Test _get_signing_key for correct behavior"""
    validator = validator_class()
    mock_client_instance = MagicMock()
    mock_client_instance.get_signing_keys.return_value = mocked_keys
    mock_pyjwk_client.return_value = mock_client_instance
    mock_get_unverified_header.return_value = {'kid': token_kid, 'alg': token_alg}

    if should_raise:
        with pytest.raises(InvalidRequestError):
            validator._get_signing_key(token, jwks_uri)
    else:
        key = validator._get_signing_key(token, jwks_uri)
        assert key.key == expected_key
