from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.test import TestCase
from unittest.mock import patch

from apps.dot_ext.constants import PATIENT_COVERAGE_SCOPES_CONSTANT
from apps.dot_ext.oauth2_validators import OAuth2Validator
from apps.dot_ext.validators import validate_uris


class TestOauth2Validators(TestCase):

    def test_validate_uris(self):
        with self.assertRaises(ValidationError):
            validate_uris('ftp://example.com/redirect')

        with self.assertRaises(ValidationError):
            validate_uris('https://example.com/redirect ftp://example')

        with self.assertRaises(ValidationError):
            validate_uris('ftp://example https://example.com/redirect')

        with self.assertRaises(ValidationError):
            validate_uris('https://example.com/redirect#tag ftp://example')

        # These don't return anything, so just run them to check for exceptions
        validate_uris('https://example.com/redirect')
        validate_uris('https://example.com/redirect https://example.org/redirect')
        validate_uris('http://example.com/redirect\nhttps://example.org/redirect')
        validate_uris('http://example.com/redirect\nhttps://example.org/redirect   ' * 72)

    def test_is_within_original_scope_invalid_request(self):
        validator = OAuth2Validator()
        request = HttpRequest()
        with patch.object(
            validator,
            'get_original_scopes',
            return_value=PATIENT_COVERAGE_SCOPES_CONSTANT
        ):
            result = validator.is_within_original_scope(['patient/ExplanationOfBenefit.rs'], object(), request)

        assert not result

    def test_is_within_original_scope_valid_request_sub_scope(self):
        validator = OAuth2Validator()
        request = HttpRequest()
        with patch.object(
            validator,
            'get_original_scopes',
            return_value=PATIENT_COVERAGE_SCOPES_CONSTANT
        ):
            result = validator.is_within_original_scope(['patient/Coverage.s'], object(), request)

        assert result

    def test_is_within_original_scope_valid_request_multi_scope_refresh_request(self):
        validator = OAuth2Validator()
        request = HttpRequest()
        with patch.object(
            validator,
            'get_original_scopes',
            return_value=PATIENT_COVERAGE_SCOPES_CONSTANT
        ):
            result = validator.is_within_original_scope(['patient/Coverage.s', 'patient/Patient.s'], object(), request)

        assert result

    def test_is_within_original_scope_invalid_request_profile(self):
        validator = OAuth2Validator()
        request = HttpRequest()
        with patch.object(
            validator,
            'get_original_scopes',
            return_value=PATIENT_COVERAGE_SCOPES_CONSTANT
        ):
            result = validator.is_within_original_scope(['profile'], object(), request)

        assert not result

    def test_is_within_original_scope_valid_request_profile(self):
        validator = OAuth2Validator()
        request = HttpRequest()
        with patch.object(
            validator,
            'get_original_scopes',
            return_value='profile patient/Patient.rs patient/Coverage.rs'
        ):
            result = validator.is_within_original_scope(['profile'], object(), request)

        assert result

    def test_is_within_original_scope_valid_request_three_resources(self):
        validator = OAuth2Validator()
        request = HttpRequest()
        with patch.object(
            validator,
            'get_original_scopes',
            return_value='patient/Patient.rs patient/Coverage.rs patient/ExplanationOfBenefit.rs'
        ):
            result = validator.is_within_original_scope(
                ['patient/ExplanationOfBenefit.r', 'patient/Coverage.s', 'patient/Patient.rs'],
                object(),
                request
            )

        assert result

    def test_is_within_original_scope_invalid_request_read_when_access_token_had_search(self):
        validator = OAuth2Validator()
        request = HttpRequest()
        with patch.object(
            validator,
            'get_original_scopes',
            return_value='patient/ExplanationOfBenefit.s'
        ):
            result = validator.is_within_original_scope(['patient/ExplanationOfBenefit.r'], object(), request)

        assert not result
