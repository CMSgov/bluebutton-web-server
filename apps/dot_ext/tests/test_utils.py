from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.dot_ext.constants import SUPPORTED_VERSION_TEST_CASES
from apps.dot_ext.utils import (
    check_samhsa_cache_and_create_access_token_extension,
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
    @patch('apps.dot_ext.utils.cache')
    def test_check_samhsa_cache_and_create_access_token_extension_use_cached_value(
        self, mock_cache, mock_access_token_extension
    ):
        """
        When cache has a value for the code and grant_type is NOT refresh_token,
        the cached value should be used for include_samhsa.
        """
        mock_cache.get.return_value = False

        check_samhsa_cache_and_create_access_token_extension(
            prior_include_samhsa=False,
            code=self.code,
            grant_type='authorization_code',
            token=self.token,
        )

        mock_access_token_extension.objects.get_or_create.assert_called_once_with(
            access_token=self.token,
            include_samhsa=False,
        )
        mock_cache.delete.assert_called_once_with(f'include_samhsa:{self.code}')

    @patch('apps.dot_ext.utils.AccessTokenExtension')
    @patch('apps.dot_ext.utils.cache')
    def test_check_samhsa_cache_and_create_access_token_extension_no_cache_value(
        self, mock_cache, mock_access_token_extension
    ):
        """
        When cache has NO value for the code and grant_type is NOT refresh_token,
        include_samhsa should default to True.
        """
        mock_cache.get.return_value = None

        check_samhsa_cache_and_create_access_token_extension(
            prior_include_samhsa=False,
            code=self.code,
            grant_type='authorization_code',
            token=self.token,
        )

        mock_access_token_extension.objects.get_or_create.assert_called_once_with(
            access_token=self.token,
            include_samhsa=True,
        )
        mock_cache.delete.assert_called_once_with(f'include_samhsa:{self.code}')

    @patch('apps.dot_ext.utils.AccessTokenExtension')
    @patch('apps.dot_ext.utils.cache')
    def test_check_samhsa_cache_and_create_access_token_extension_refresh_token_grant(
        self, mock_cache, mock_access_token_extension
    ):
        """
        When grant_type is 'refresh_token', prior_include_samhsa=False
        should override any cache value.
        """
        mock_cache.get.return_value = True

        check_samhsa_cache_and_create_access_token_extension(
            prior_include_samhsa=False,
            code=self.code,
            grant_type='refresh_token',
            token=self.token,
        )

        mock_access_token_extension.objects.get_or_create.assert_called_once_with(
            access_token=self.token,
            include_samhsa=False,
        )
        mock_cache.delete.assert_called_once_with(f'include_samhsa:{self.code}')
