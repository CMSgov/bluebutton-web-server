from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.test import TestCase

from apps.constants import CLIENT_CREDENTIALS, REFRESH_TOKEN, TEST_APP_CLIENT_ID
from apps.dot_ext.constants import V2_SCOPES_ALL
from apps.dot_ext.oauth2_validators import OAuth2Validator, SingleAccessTokenValidator
from apps.dot_ext.validators import validate_uris

PATIENT_COVERAGE_SCOPES = 'patient/Patient.rs patient/Coverage.rs'


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
        with patch.object(validator, 'get_original_scopes', return_value=PATIENT_COVERAGE_SCOPES):
            result = validator.is_within_original_scope(['patient/ExplanationOfBenefit.rs'], object(), request)

        assert not result

    def test_is_within_original_scope_valid_request_sub_scope(self):
        validator = OAuth2Validator()
        request = HttpRequest()
        with patch.object(validator, 'get_original_scopes', return_value=PATIENT_COVERAGE_SCOPES):
            result = validator.is_within_original_scope(['patient/Coverage.s'], object(), request)

        assert result

    def test_is_within_original_scope_valid_request_multi_scope_refresh_request(self):
        validator = OAuth2Validator()
        request = HttpRequest()
        with patch.object(validator, 'get_original_scopes', return_value=PATIENT_COVERAGE_SCOPES):
            result = validator.is_within_original_scope(['patient/Coverage.s', 'patient/Patient.s'], object(), request)

        assert result

    def test_is_within_original_scope_invalid_request_profile(self):
        validator = OAuth2Validator()
        request = HttpRequest()
        with patch.object(validator, 'get_original_scopes', return_value=PATIENT_COVERAGE_SCOPES):
            result = validator.is_within_original_scope(['profile'], object(), request)

        assert not result

    def test_is_within_original_scope_valid_request_profile(self):
        validator = OAuth2Validator()
        request = HttpRequest()
        with patch.object(
            validator, 'get_original_scopes', return_value='profile patient/Patient.rs patient/Coverage.rs'
        ):
            result = validator.is_within_original_scope(['profile'], object(), request)

        assert result

    def test_is_within_original_scope_valid_request_three_resources(self):
        validator = OAuth2Validator()
        request = HttpRequest()
        with patch.object(
            validator,
            'get_original_scopes',
            return_value='patient/Patient.rs patient/Coverage.rs patient/ExplanationOfBenefit.rs',
        ):
            result = validator.is_within_original_scope(
                ['patient/ExplanationOfBenefit.r', 'patient/Coverage.s', 'patient/Patient.rs'], object(), request
            )

        assert result

    def test_is_within_original_scope_invalid_request_read_when_access_token_had_search(self):
        validator = OAuth2Validator()
        request = HttpRequest()
        with patch.object(validator, 'get_original_scopes', return_value='patient/ExplanationOfBenefit.s'):
            result = validator.is_within_original_scope(['patient/ExplanationOfBenefit.r'], object(), request)

        assert not result


@pytest.mark.django_db
@pytest.mark.parametrize(
    'scopes, grant_type',
    [
        (['patient/ExplanationOfBenefit.rs', 'patient/Patient.rs'], CLIENT_CREDENTIALS),
        (['patient/ExplanationOfBenefit.rs', 'patient/Coverage.rs'], CLIENT_CREDENTIALS),
        (['patient/AuditEvent.rs', 'patient/Patient.rs'], CLIENT_CREDENTIALS),
        (['patient/AuditEvent.r'], CLIENT_CREDENTIALS),
        (['patient/AuditEvent.rs'], CLIENT_CREDENTIALS),
        (['profile', 'patient/Coverage.r'], CLIENT_CREDENTIALS),
        (['profile', 'patient/Coverage.r'], CLIENT_CREDENTIALS),
        (['patient/ExplanationOfBenefit.rs', 'patient/Patient.rs'], REFRESH_TOKEN),
        (['patient/ExplanationOfBenefit.rs', 'patient/Coverage.rs'], REFRESH_TOKEN),
        (['patient/ExplanationOfBenefit.rs', 'patient/Patient.rs'], 'authorization-code'),
        (['patient/ExplanationOfBenefit.rs', 'patient/Coverage.rs'], 'authorization-code'),
    ],
)
def test_validate_scopes(create_application, scopes, grant_type):
    """Ensure that the overwritten validate_scopes function processes our standard scopes (EOB, Coverage, Patient)
    and the AuditEvent scopes correctly. AuditEvent scopes have default equal to false and are not added to applications
    (as of July 2026), so we have custom handling for those.

    Args:
        scopes: List of scopes we are validating will go through the overwritten OAuth2 function
        successfully
    """
    validator = SingleAccessTokenValidator()
    with patch.object(OAuth2Validator, 'validate_scopes', return_value=True):
        with patch.object(validator, 'get_original_scopes', return_value=V2_SCOPES_ALL):
            app = create_application('TestApp')
            request = HttpRequest()
            request.grant_type = grant_type
            client_id = TEST_APP_CLIENT_ID
            result = validator.validate_scopes(client_id, scopes, app, request)

            assert result
