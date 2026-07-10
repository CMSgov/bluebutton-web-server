import os
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase
from oauthlib.oauth2.rfc6749.errors import InvalidClientError

from apps.dot_ext.constants import SUPPORTED_VERSION_TEST_CASES
from apps.dot_ext.models import AuthFlowTracking
from apps.dot_ext.utils import (
    check_auth_tracking_and_create_access_token_extension,
    check_can_token_scope_for_audit_event_scopes,
    get_api_version_number_from_url,
    remove_application_user_pair_tokens_data_access,
    validate_client_id,
    validate_latin_extended_string,
)
from apps.versions import VersionNotMatched


class TestDOTUtils(TestCase):
    def setUp(self):
        self.token = MagicMock()
        self.code = 'test_code'
        self.prior_include_samhsa = False

    def test_get_api_version_number(self):
        for test in SUPPORTED_VERSION_TEST_CASES:
            result = get_api_version_number_from_url(test['url_path'])
            assert result == test['expected']

    def test_get_api_version_number_unsupported_version(self):
        # unsupported version will raise an exception
        with self.assertRaises(VersionNotMatched, msg='4 extracted from /v4/fhir/Coverage/'):
            get_api_version_number_from_url('/v4/fhir/Coverage/')

    def test_latin_extended_success(self):
        valid_inputs = ['HelloWorld123!', 'naïve café über', chr(383), f'valid{chr(383)}']

        for text in valid_inputs:
            assert validate_latin_extended_string(text)

    def test_latin_extended_failure(self):
        invalid_inputs = [
            'Hello 🌍',
            'Привет',
            'こんにちは',
            chr(384),
            f'invalid{chr(384)}',
        ]

        for text in invalid_inputs:
            assert not validate_latin_extended_string(text)

    @patch('apps.dot_ext.utils.AccessTokenExtension')
    @patch('apps.dot_ext.utils.AuthFlowTracking.objects.get')
    def test_check_auth_tracking_and_create_access_token_extension_use_database_value(
        self, mock_auth_flow_tracking, mock_access_token_extension
    ):
        """
        When dot_ext_auth_flow_tracking has a record for the code and grant_type is NOT refresh_token,
        the dot_ext_auth_flow_tracking.include_samhsa value should be used for include_samhsa.
        """
        tracking_object = AuthFlowTracking.objects.create(
            code=self.code,
            include_samhsa=False,
            expires=datetime.now(UTC),
        )
        mock_auth_flow_tracking.return_value = tracking_object

        check_auth_tracking_and_create_access_token_extension(
            prior_include_samhsa=False,
            code=self.code,
            grant_type='authorization_code',
            token=self.token,
            prior_part_d_eob_only=False,
        )

        mock_access_token_extension.objects.get_or_create.assert_called_once_with(
            access_token=self.token,
            include_samhsa=False,
            part_d_eob_only=False,
        )

    @patch('apps.dot_ext.utils.AccessTokenExtension')
    @patch('apps.dot_ext.utils.AuthFlowTracking.objects.get')
    def test_check_auth_tracking_and_create_access_token_extension_use_database_value_true(
        self, mock_auth_flow_tracking, mock_access_token_extension
    ):
        """
        When dot_ext_auth_flow_tracking has a record for the code and grant_type is NOT refresh_token,
        the dot_ext_auth_flow_tracking.include_samhsa value should be used for include_samhsa.
        """
        tracking_object = AuthFlowTracking.objects.create(
            code=self.code,
            include_samhsa=True,
            expires=datetime.now(UTC),
        )
        mock_auth_flow_tracking.return_value = tracking_object

        check_auth_tracking_and_create_access_token_extension(
            prior_include_samhsa=True,
            code=self.code,
            grant_type='authorization_code',
            token=self.token,
            prior_part_d_eob_only=False,
        )

        mock_access_token_extension.objects.get_or_create.assert_called_once_with(
            access_token=self.token,
            include_samhsa=True,
            part_d_eob_only=False,
        )

    @patch('apps.dot_ext.utils.AccessTokenExtension')
    @patch('apps.dot_ext.utils.AuthFlowTracking.objects.get')
    def test_check_auth_tracking_and_create_access_token_extension_no_database_value(
        self, mock_auth_flow_tracking, mock_access_token_extension
    ):
        """
        When there is no dot_ext_auth_flow_tracking record, just use the default of True
        """
        mock_auth_flow_tracking.side_effect = AuthFlowTracking.DoesNotExist

        check_auth_tracking_and_create_access_token_extension(
            prior_include_samhsa=True,
            code=self.code,
            grant_type='authorization_code',
            token=self.token,
            prior_part_d_eob_only=False,
        )

        mock_access_token_extension.objects.get_or_create.assert_called_once_with(
            access_token=self.token,
            include_samhsa=True,
            part_d_eob_only=False,
        )

    @patch('apps.dot_ext.utils.AccessTokenExtension')
    @patch('apps.dot_ext.utils.AuthFlowTracking.objects.get')
    def test_check_auth_tracking_and_create_access_token_extension_refresh_token_grant(
        self, mock_auth_flow_tracking, mock_access_token_extension
    ):
        """
        When grant_type is 'refresh_token', prior_include_samhsa=False
        should override any dot_ext_auth_flow_tracking record include_samhsa value.
        """
        tracking_object = AuthFlowTracking.objects.create(
            code=self.code,
            include_samhsa=True,
            expires=datetime.now(UTC),
        )
        mock_auth_flow_tracking.return_value = tracking_object

        check_auth_tracking_and_create_access_token_extension(
            prior_include_samhsa=False,
            code=self.code,
            grant_type='refresh_token',
            token=self.token,
            prior_part_d_eob_only=False,
        )

        mock_access_token_extension.objects.get_or_create.assert_called_once_with(
            access_token=self.token,
            include_samhsa=False,
            part_d_eob_only=False,
        )

    @patch('apps.dot_ext.utils.AccessToken')
    @patch('apps.dot_ext.utils.DataAccessGrant')
    @patch('apps.dot_ext.utils.RefreshToken')
    def test_remove_application_user_pair_tokens_data_access_delete_access_tokens_not_grant(
        self, mock_refresh_token, mock_data_access_grant, mock_access_token
    ) -> None:
        application = MagicMock()
        user = MagicMock()
        access_token_queryset = MagicMock()
        mock_access_token.objects.filter.return_value = access_token_queryset
        data_access_grant_queryset = MagicMock()
        mock_data_access_grant.objects.filter.return_value = data_access_grant_queryset
        refresh_token_queryset = MagicMock()
        mock_refresh_token.objects.filter.return_value = refresh_token_queryset

        remove_application_user_pair_tokens_data_access(application, user, False, True)

        mock_access_token.objects.filter.assert_called_once_with(application=application, user=user)
        access_token_queryset.delete.assert_called_once()

        data_access_grant_queryset.delete.assert_not_called()

        mock_refresh_token.objects.filter.assert_called_once_with(application=application, user=user)
        refresh_token_queryset.delete.assert_called_once()


@pytest.mark.parametrize(
    'client_id',
    [
        'short',
        '',
        'a' * 39,
        'a' * 41,
        'abcdefghijklmnopqrstuvwxyz12345678901234!',  # 40 chars with special char
        'abcdefghijklmnopqrstuvwxyz1234567890123 ',  # 40 chars with space
        '../../../etc/' + 'a' * 27,  # path traversal attempt
        "'; DROP TABLE not_a_real_table;--",  # SQL injection attempt
    ],
    ids=[
        'too_short',
        'empty',
        '39_chars',
        '41_chars',
        'special_char',
        'contains_space',
        'path_traversal',
        'sql_injection',
    ],
)
def test_validate_client_id_rejects_invalid(client_id):
    with patch.dict(os.environ, {'TARGET_ENV': 'test'}):
        with pytest.raises(InvalidClientError):
            validate_client_id(client_id)


@pytest.mark.parametrize(
    'client_id',
    [
        'a' * 40,
        'A' * 40,
        '0' * 40,
        'aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3wX4y5Z0',
    ],
    ids=['lowercase', 'uppercase', 'digits', 'mixed'],
)
def test_validate_client_id_accepts_valid(client_id):
    # Should not raise
    with patch.dict(os.environ, {'TARGET_ENV': 'test'}):
        validate_client_id(client_id)


@pytest.mark.parametrize(
    'passed_in_scope, expected_scope',
    [
        (
            'profile patient/Patient.rs patient/AuditEvent.rs patient/AuditEvent.r',
            'profile patient/Patient.rs patient/AuditEvent.rs',
        ),
        (
            'profile patient/Patient.rs patient/AuditEvent.rs patient/AuditEvent.s',
            'profile patient/Patient.rs patient/AuditEvent.rs',
        ),
        ('profile patient/Patient.rs patient/AuditEvent.r', 'profile patient/Patient.rs patient/AuditEvent.rs'),
        ('profile patient/Patient.rs patient/AuditEvent.s', 'profile patient/Patient.rs patient/AuditEvent.rs'),
        ('profile patient/Patient.rs', 'profile patient/Patient.rs patient/AuditEvent.rs'),
        (
            'profile patient/Patient.rs patient/AuditEvent.s patient/AuditEvent.r',
            'profile patient/Patient.rs patient/AuditEvent.rs',
        ),
        (
            'profile patient/Patient.rs patient/AuditEvent.s patient/AuditEvent.r patient/AuditEvent.rs',
            'profile patient/Patient.rs patient/AuditEvent.rs',
        ),
        ('profile patient/Patient.rs patient/AuditEvent.rs', 'profile patient/Patient.rs patient/AuditEvent.rs'),
    ],
)
def test_check_can_token_scope_for_audit_event_scopes(passed_in_scope, expected_scope) -> None:
    """Confirm that no matter what combination of AuditEvent scopes is passed into
    check_can_token_scope_for_audit_event_scopes, that only patient/AuditEvent.rs is present
    on the returned scope.
    Args:
        passed_in_scope (_type_): scope being passed into check_can_token_scope_for_audit_event_scopes
        expected_scope (_type_): expected scope to be returned
    """
    scope = check_can_token_scope_for_audit_event_scopes(passed_in_scope)
    assert scope == expected_scope
