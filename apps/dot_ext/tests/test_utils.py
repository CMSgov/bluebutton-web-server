from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.dot_ext.constants import SUPPORTED_VERSION_TEST_CASES
from apps.dot_ext.utils import (
    get_api_version_number_from_url,
    remove_application_user_pair_tokens_data_access,
    validate_latin_extended_string,
)
from apps.versions import VersionNotMatched


class TestDOTUtils(TestCase):
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
