from django.test import TestCase

from apps.versions import VersionNotMatched
from apps.dot_ext.constants import SUPPORTED_VERSION_TEST_CASES
from apps.dot_ext.utils import get_api_version_number_from_url, validate_latin_extended_string


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
        valid_inputs = [
            "HelloWorld123!",
            "naïve café über",
            chr(383),
            f"valid{chr(383)}"
        ]

        for text in valid_inputs:
            assert validate_latin_extended_string(text)

    def test_latin_extended_failure(self):
        invalid_inputs = [
            "Hello 🌍",
            "Привет",
            "こんにちは"
            "",
            chr(384),
            f"invalid{chr(384)}",
        ]

        for text in invalid_inputs:
            assert not validate_latin_extended_string(text)
