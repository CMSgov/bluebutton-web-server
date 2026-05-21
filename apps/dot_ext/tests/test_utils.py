from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from apps.dot_ext.constants import SUPPORTED_VERSION_TEST_CASES
from apps.dot_ext.utils import (
    get_api_version_number_from_url,
    revoke_prior_tokens_for_user_and_app_if_they_exist,
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

    @patch('apps.dot_ext.utils.get_refresh_token_model')
    @patch('apps.dot_ext.utils.get_access_token_model')
    def test_revoke_prior_tokens_for_user_and_app_if_they_exist_no_prior_tokens(
        self, mock_get_access_token, mock_get_refresh_token
    ):
        """Confirm that if only one access token is returned, that we never query for refresh tokens"""
        mock_access_token_model = MagicMock()
        mock_access_token_model.objects.filter.return_value.order_by.return_value = [MagicMock()]
        mock_get_access_token.return_value = mock_access_token_model

        mock_refresh_token_model = MagicMock()
        mock_get_refresh_token.return_value = mock_refresh_token_model

        revoke_prior_tokens_for_user_and_app_if_they_exist(1, 1)

        mock_get_refresh_token.objects.get.assert_not_called()

    @patch('apps.dot_ext.utils.timezone')
    @patch('apps.dot_ext.utils.get_refresh_token_model')
    @patch('apps.dot_ext.utils.get_access_token_model')
    def test_revoke_prior_tokens_for_user_and_app_if_they_exist_prior_tokens_exit(
        self, mock_get_access_token, mock_get_refresh_token, mock_timezone
    ):
        """Confirm that if there are multiple access tokens, the prior ones will have their expires value updated.
        Also, any associated refresh tokens will have their access_token_id set to null, and their revoked value
        set to the current time (UTC)
        """
        mock_timezone.now.return_value = timezone.now()

        new_access_token = MagicMock(
            id=1, user_id=1, expires=timezone.now() + timedelta(hours=2), created=timezone.now()
        )
        prior_access_token = MagicMock(
            id=2, user_id=1, expires=timezone.now() + timedelta(minutes=30), created=timezone.now() - timedelta(days=10)
        )
        prior_access_token_two = MagicMock(
            id=3, user_id=1, expires=timezone.now() - timedelta(days=20), created=timezone.now() - timedelta(days=20)
        )

        mock_access_token_model = MagicMock()
        mock_access_token_model.objects.filter.return_value.order_by.return_value = [
            new_access_token,
            prior_access_token,
            prior_access_token_two,
        ]
        mock_get_access_token.return_value = mock_access_token_model

        refresh_token = MagicMock(access_token_id=2, revoked=None)
        mock_refresh_token_model = MagicMock()
        mock_refresh_token_model.objects.get.return_value = refresh_token
        mock_get_refresh_token.return_value = mock_refresh_token_model

        revoke_prior_tokens_for_user_and_app_if_they_exist(1, 10)

        prior_access_token.save.assert_called_once()
        prior_access_token_two.save.assert_not_called()

        assert refresh_token.revoked is not None
        assert refresh_token.access_token_id is None
        refresh_token.save.assert_called_once()

    @patch('apps.dot_ext.utils.timezone')
    @patch('apps.dot_ext.utils.get_access_token_model')
    def test_revoke_prior_tokens_for_user_and_app_if_they_exist_no_associated_refresh_token(
        self, mock_get_access_token, mock_timezone
    ):
        """Confirm that even if there is no associated refresh_token for an access_token, that the access_token
        still has its expires value updated.
        """
        mock_timezone.now.return_value = timezone.now()

        new_access_token = MagicMock(
            id=1, user_id=1, expires=timezone.now() + timedelta(hours=2), created=timezone.now()
        )
        prior_access_token = MagicMock(
            id=2, user_id=1, expires=timezone.now() + timedelta(minutes=30), created=timezone.now() - timedelta(days=10)
        )

        mock_access_token_model = MagicMock()
        mock_access_token_model.objects.filter.return_value.order_by.return_value = [
            new_access_token,
            prior_access_token,
        ]
        mock_get_access_token.return_value = mock_access_token_model

        revoke_prior_tokens_for_user_and_app_if_they_exist(1, 10)
        prior_access_token.save.assert_called_once()
