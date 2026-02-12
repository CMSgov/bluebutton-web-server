from apps.fhir.constants import (
    Appropriate,
    MissingFields,
    Status,
    BASEURL,
    PAGE_NOT_FOUND_TESTS,
    TESTS,
)
from apps.test import BaseApiTest

from django.conf import settings
from django.test.client import Client
from oauth2_provider.models import get_access_token_model
from unittest import skipIf
from waffle.testutils import override_switch, override_flag


AccessToken = get_access_token_model()


class BlueButtonTestEndpoints(BaseApiTest):

    def setUp(self):
        self.client = Client()
        self.read_capability = self._create_capability('Read', [])
        self.write_capability = self._create_capability('Write', [])

    @skipIf((not settings.RUN_ONLINE_TESTS), 'Can\'t reach external sites.')
    @override_switch('v3_endpoints', active=True)
    @override_flag('v3_early_adopter', active=False)
    def test_userinfo_returns_403(self):
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=settings.DEFAULT_SAMPLE_FHIR_ID_V2)
        ac = AccessToken.objects.get(token=first_access_token)
        ac.save()

        response = self.client.get(
            f'{BASEURL}/v3/connect/userinfo',
            Authorization='Bearer %s' % (first_access_token))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['detail'], settings.APPLICATION_DOES_NOT_HAVE_V3_ENABLED_YET.format('John_Smith_test'))

    @skipIf((not settings.RUN_ONLINE_TESTS), 'Can\'t reach external sites.')
    @override_switch('v3_endpoints', active=True)
    @override_flag('v3_early_adopter', active=True)
    def test_userinfo_returns_200(self):
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=settings.DEFAULT_SAMPLE_FHIR_ID_V2)
        ac = AccessToken.objects.get(token=first_access_token)
        ac.save()

        response = self.client.get(
            f'{BASEURL}/v3/connect/userinfo',
            Authorization='Bearer %s' % (first_access_token))
        self.assertEqual(response.status_code, 200)

    # This makes sure URLs return 200s.
    @skipIf((not settings.RUN_ONLINE_TESTS), "Can't reach external sites.")
    def test_url_status_codes(self):
        with override_switch('v3_endpoints', active=True):
            for test in TESTS:
                if isinstance(test, Appropriate) or isinstance(test, Status) or isinstance(test, MissingFields):
                    response = self.client.get(f'{BASEURL}/{test.url}')
                    self.assertEqual(response.status_code, test.status_code)

    # This looks at the given set of URLs and makes sure that the version value encoded in the
    # reponses are correctly versioned. Note the handling of v1/v2.
    @skipIf((not settings.RUN_ONLINE_TESTS), "Can't reach external sites.")
    @override_switch('v3_endpoints', active=True)
    def test_urls_appropriate(self):
        for test in TESTS:
            if isinstance(test, Appropriate):
                response = self.client.get(f'{BASEURL}/{test.url}')
                if response.status_code == test.status_code:
                    the_json = response.json()

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

    @skipIf((not settings.RUN_ONLINE_TESTS), "Can't reach external sites.")
    @override_switch('v3_endpoints', active=True)
    def test_smart_configuration_missing_fields_in_v3(self):
        for test in TESTS:
            if isinstance(test, MissingFields):
                response = self.client.get(f'{BASEURL}/{test.url}')
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
    # is commented above for reference.

    @skipIf((not settings.RUN_ONLINE_TESTS), "Can't reach external sites.")
    @override_switch('v3_endpoints', active=True)
    def test_fhir_metadata_extensions_have_v3(self):
        the_url = f'{BASEURL}/v3/fhir/metadata'
        response = self.client.get(the_url)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertIn('v3', json['implementation']['url'])
        for obj in json['rest']:
            for ext in obj['security']['extension']:
                for e in ext['extension']:
                    self.assertIn('v3', e['valueUri'])

    @skipIf((not settings.RUN_ONLINE_TESTS), 'Can\'t reach external sites.')
    @override_switch('v3_endpoints', active=False)
    def test_page_not_found_when_waffle_switch_disabled(self):
        for test in PAGE_NOT_FOUND_TESTS:
            response = self.client.get(f'{BASEURL}/' + test.url)
            self.assertEqual(response.status_code, test.status_code)
