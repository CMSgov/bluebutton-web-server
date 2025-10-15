from apps.test import BaseApiTest

from collections import namedtuple as NT
from django.conf import settings
from django.test.client import Client
from httmock import all_requests, HTTMock
from oauth2_provider.models import get_access_token_model
import os
import requests
from unittest import skipIf

# Introduced in bb2-4184
# Rudimentary tests to make sure endpoints exist and are returning
# basic responses that make sense. Not a deep test.
#
# PRECONDITION
# You must be on the VPN. Tested against TEST w.r.t. certs.

# Ensure that the status_code, version, and other attributes of the response are valid
Appropriate = NT('Status', 'url,version,status_code')
# Ensure the correct status_code is returned for a given endpoint
Status = NT('Status', 'url,status_code')
# These test cases ensure that certain fields are not present in the response for a given endpoint
MissingFields = NT('MissingFields', 'url,version,fields,status_code')

AccessToken = get_access_token_model()

BASEURL = 'http://localhost:8000'
TESTS = [
    Appropriate('v1/connect/.well-known/openid-configuration', 'v1', 200),
    Appropriate('v2/connect/.well-known/openid-configuration', 'v2', 200),
    Appropriate('v3/connect/.well-known/openid-configuration', 'v3', 200),
    MissingFields('v3/fhir/.well-known/smart-configuration', 'v3', ['fhir_metadata_uri', 'userinfo_endpoint'], 200),
    Status('.well-known/openid-configuration', 200),
    Status('.well-known/openid-configuration-v2', 200)
]
FHIR_ID_V2 = settings.DEFAULT_SAMPLE_FHIR_ID_V2


class BlueButtonTestEndpoints(BaseApiTest):

    def setUp(self):
        self.client = Client()
        self.read_capability = self._create_capability('Read', [])
        self.write_capability = self._create_capability('Write', [])

    @skipIf(os.getenv('DO_NOT_RUN_ONLINE_TESTS'), 'Can\'t reach external sites.')
    def test_userinfo_returns_200(self):
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)
        ac = AccessToken.objects.get(token=first_access_token)
        ac.save()

        @all_requests
        def catchall(url, req):
            return {'status_code': 200,
                    'content': {
                        'sub': FHIR_ID_V2,
                        'name': ' ',
                        'given_name': '',
                        'family_name': '',
                        'email': '',
                        'iat': '2025-10-14T18:01:01.660Z',
                        'patient': FHIR_ID_V2
                    }}

        with HTTMock(catchall):
            response = self.client.get(
                f'{BASEURL}/v3/connect/userinfo',
                Authorization='Bearer %s' % (first_access_token))
            self.assertEqual(response.status_code, 200)

    # This makes sure URLs return 200s.
    @skipIf(os.getenv('DO_NOT_RUN_ONLINE_TESTS'), 'Can\'t reach external sites.')
    def test_url_status_codes(self):
        for test in TESTS:
            if isinstance(test, Appropriate) or isinstance(test, Status) or isinstance(test, MissingFields):
                response = requests.get(f'{BASEURL}/{test.url}')
                self.assertEqual(response.status_code, test.status_code)

    # This looks at the given set of URLs and makes sure that the version value encoded in the
    # reponses are correctly versioned. Note the handling of v1/v2.
    @skipIf(os.getenv('DO_NOT_RUN_ONLINE_TESTS'), 'Can\'t reach external sites.')
    def test_urls_appropriate(self):
        for test in TESTS:
            if isinstance(test, Appropriate):
                response = requests.get(f'{BASEURL}/{test.url}')
                if response.status_code == test.status_code:
                    the_json = response.json()
                    # These should match the version, and connect should be present as well
                    # to be SMART on FHIR compliant
                    for field in ['issuer']:
                        self.assertIn(test.version + '/connect/', the_json[field])

                    # These will be v2 for all v1 urls
                    if test.version == 'v1':
                        version = 'v2'
                    else:
                        version = test.version

                    for field in ['authorization_endpoint',
                                  'revocation_endpoint',
                                  'token_endpoint',
                                  'userinfo_endpoint',
                                  'fhir_metadata_uri']:
                        self.assertIn(version, the_json[field])
                else:
                    self.fail('Failed to connect with a good status code.')

    @skipIf(os.getenv('DO_NOT_RUN_ONLINE_TESTS'), 'Can\'t reach external sites.')
    def test_smart_configuration_missing_fields_in_v3(self):
        for test in TESTS:
            if isinstance(test, MissingFields):
                response = requests.get(f'{BASEURL}/{test.url}')
                if response.status_code == 200:
                    the_json = response.json()
                    for field in test.fields:
                        self.assertNotIn(field, the_json)
                else:
                    self.fail('Failed to connect with status 200')

    # 'extension': [
    #     {
    #         'url': 'http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris',
    #         'extension': [
    #             {
    #                 'url': 'token',
    #                 'valueUri': 'http://localhost:8000/v3/o/token'
    #             },
    #             {
    #                 'url': 'authorize',
    #                 'valueUri': 'http://localhost:8000/v3/o/authorize'
    #             },
    #             {
    #                 'url': 'revoke',
    #                 'valueUri': 'http://localhost:8000/v3/o/revoke_token'
    #             }
    #         ]
    #     }
    # ]
    # Make sure FHIR v3 extensions are correct when the metadata is fetched; the extensions object
    # is commented above for reference. This would be a good use of jsonpath in our codebase...
    @skipIf(os.getenv('DO_NOT_RUN_ONLINE_TESTS'), 'Can\'t reach external sites.')
    def test_fhir_metadata_extensions_have_v3(self):
        response = requests.get(f'{BASEURL}/v3/fhir/metadata')
        if response.status_code == 200:
            json = response.json()
            self.assertIn('v3', json['implementation']['url'])
            for obj in json['rest']:
                for ext in obj['security']['extension']:
                    for e in ext['extension']:
                        self.assertIn('v3', e['valueUri'])
