import datetime
from datetime import timezone

# from unittest.mock import patch
import pytest

# from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase

# from freezegun import freeze_time
# from waffle.testutils import override_switch
from apps.dot_ext.constants import ASYMMETRIC_AUTH_REQUIRED_CLAIM_FIELDS, CAN_REQUIRED_CLAIM_FIELDS
from apps.dot_ext.validators import (
    AsymmetricAuthValidator,
    CMSAlignedNetworksValidator,
    validate_url,
)

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


class TestCommonTokenValidatorBehavior(TestCase):
    @pytest.mark.parametrize(
        'validator_class, expected_fields',
        [
            (AsymmetricAuthValidator, ASYMMETRIC_AUTH_REQUIRED_CLAIM_FIELDS),
            (CMSAlignedNetworksValidator, CAN_REQUIRED_CLAIM_FIELDS),
        ],
    )
    def test_get_required_fields(self, validator_class, expected_fields):
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
    def test_get_waffle_switch(self, validator_class, waffle_switch):
        """Test that the validator returns the correct waffle switch."""
        validator = validator_class()
        assert validator.get_waffle_switch() == waffle_switch

    # @patch('apps.dot_ext.validators._decode_and_validate_token.get_')
    # @pytest.mark.parametrize('validator_class', [AsymmetricAuthValidator, CMSAlignedNetworksValidator])
    # @pytest.mark.parametrize(
    #     'missing_field, expected_result, error',
    #     [
    #         ('iss', False, 'Missing required field: iss'),
    #         ('sub', False, 'Missing required field: sub'),
    #         ('aud', False, 'Missing required field: aud'),
    #         ('jti', False, 'Missing required field: jti'),
    #         ('exp', False, 'Missing required field: exp'),
    #     ],
    # )
    # def test_shared_fields_validation(
    #     self,
    #     validator_class,
    #     missing_field,
    #     expected_result,
    #     error,
    # ):
    #     payload = ASYMMETRIC_AUTH_PAYLOAD.copy()
    #     payload.pop(missing_field, None)
    #     validator = validator_class()
    #     if expected_result:
    #         try:
    #             validator.validate(payload)
    #         except ValidationError:
    #             self.fail(f'validate() raised ValidationError unexpectedly for missing field {missing_field}')
    #     else:
    #         with self.assertRaises(ValidationError, msg=f'Expected failure for missing field {missing_field}'):
    #             validator.validate(payload)
