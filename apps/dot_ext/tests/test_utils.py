from django.test import TestCase

from apps.versions import VersionNotMatched
from ..utils import get_api_version_number_from_url

SUPPORTED_VERSION_TEST_CASES = [
    {'url_path': '/v2/fhir/Patient/', 'expected': 2},
    # return 0 because v2 does not have a leading /
    {'url_path': 'v2/fhir/Patient/', 'expected': 0},
    {'url_path': '/v3/fhir/Coverage/', 'expected': 3},
    {'url_path': '/v3/fhir/Coverage/v2/', 'expected': 3},
]


class TestDOTUtils(TestCase):
    def test_get_api_version_number(self):
        for test in SUPPORTED_VERSION_TEST_CASES:
            result = get_api_version_number_from_url(test['url_path'])
            assert result == test['expected']

    def test_get_api_version_number_unsupported_version(self):
        # unsupported version will raise an exception
        with self.assertRaises(VersionNotMatched, msg='4 extracted from /v4/fhir/Coverage/'):
            get_api_version_number_from_url('/v4/fhir/Coverage/')
