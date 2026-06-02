from datetime import datetime
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.dot_ext.constants import SUPPORTED_VERSION_TEST_CASES
from apps.dot_ext.models import AuthFlowTracking
from apps.dot_ext.utils import (
    check_auth_tracking_and_create_access_token_extension,
    get_api_version_number_from_url,
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
            expires=datetime.now(),
        )
        mock_auth_flow_tracking.return_value = tracking_object

        check_auth_tracking_and_create_access_token_extension(
            prior_include_samhsa=False,
            code=self.code,
            grant_type='authorization_code',
            token=self.token,
        )

        mock_access_token_extension.objects.get_or_create.assert_called_once_with(
            access_token=self.token,
            include_samhsa=False,
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
            expires=datetime.now(),
        )
        mock_auth_flow_tracking.return_value = tracking_object

        check_auth_tracking_and_create_access_token_extension(
            prior_include_samhsa=True,
            code=self.code,
            grant_type='authorization_code',
            token=self.token,
        )

        mock_access_token_extension.objects.get_or_create.assert_called_once_with(
            access_token=self.token,
            include_samhsa=True,
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
        )

        mock_access_token_extension.objects.get_or_create.assert_called_once_with(
            access_token=self.token,
            include_samhsa=True,
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
            expires=datetime.now(),
        )
        mock_auth_flow_tracking.return_value = tracking_object

        check_auth_tracking_and_create_access_token_extension(
            prior_include_samhsa=False,
            code=self.code,
            grant_type='refresh_token',
            token=self.token,
        )

        mock_access_token_extension.objects.get_or_create.assert_called_once_with(
            access_token=self.token,
            include_samhsa=False,
        )
