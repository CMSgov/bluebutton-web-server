import json

from django.test.client import Client
from django.urls import reverse
from httmock import all_requests, HTTMock
from oauth2_provider.models import get_access_token_model
from waffle.testutils import override_switch, override_flag

from apps.test import BaseApiTest
from apps.mymedicare_cb.tests.responses import patient_response

AccessToken = get_access_token_model()


def get_expected_read_request(ver):
    return {'method': 'GET',
            'url': 'https://fhir.backend.bluebutton.hhsdevcloud.us/{}/fhir/Patient/-20140000008325/?_format=json'.format(ver),
            'headers': {
                'User-Agent': 'python-requests/2.20.0',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'Connection': 'keep-alive',
                'BlueButton-OriginalQueryCounter': '1',
                'BlueButton-BeneficiaryId': 'patientId:-20140000008325',
                'BlueButton-Application': 'John_Smith_test',
                'X-Forwarded-For': '127.0.0.1',
                'keep-alive': 'timeout=120, max=10',
                'BlueButton-OriginalUrl': '/{}/fhir/Patient/-20140000008325'.format(ver),
                'BlueButton-BackendCall': ('https://fhir.backend.bluebutton.hhsdevcloud.us'
                                           '/{}/fhir/Patient/-20140000008325/').format(ver), }
            }


def get_expected_request(ver):
    return {'method': 'GET',
            'url': ("https://fhir.backend.bluebutton.hhsdevcloud.us/"
                    "{}/fhir/Patient/?_format=application%2Fjson%2Bfhir&_id=-20140000008325".format(ver)),
            'headers': {
                'User-Agent': 'python-requests/2.20.0',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'Connection': 'keep-alive',
                'BlueButton-OriginalQueryCounter': '1',
                'BlueButton-BeneficiaryId': 'patientId:-20140000008325',
                'BlueButton-Application': 'John_Smith_test',
                'X-Forwarded-For': '127.0.0.1',
                'keep-alive': 'timeout=120, max=10',
                'BlueButton-OriginalUrl': '/{}/fhir/Patient'.format(ver),
                'BlueButton-BackendCall': 'https://fhir.backend.bluebutton.hhsdevcloud.us/{}/fhir/Patient/'.format(ver), }
            }


class FHIRResourcesReadSearchTest(BaseApiTest):

    def setUp(self):
        # create read and write capabilities
        self.read_capability = self._create_capability('Read', [])
        self.write_capability = self._create_capability('Write', [])
        self._create_capability('patient', [
            ["GET", r"\/v1\/fhir\/Patient\/\-\d+"],
            ["GET", r"\/v1\/fhir\/Patient\/\d+"],
            ["GET", "/v1/fhir/Patient"],
        ])
        self._create_capability('coverage', [
            ["GET", r"\/v1\/fhir\/Coverage\/.+"],
            ["GET", "/v1/fhir/Coverage"],
        ])
        self._create_capability('eob', [
            ["GET", r"\/v1\/fhir\/ExplanationOfBenefit\/.+"],
            ["GET", "/v1/fhir/ExplanationOfBenefit"],
        ])
        # Setup the RequestFactory
        self.client = Client()

    def test_search_patient_request(self):
        self._search_patient_request(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
    def test_search_patient_request_v2(self):
        self._search_patient_request(True)

    def _search_patient_request(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')
        ver = 'v1' if not v2 else 'v2'
        expected_request = get_expected_request(ver)

        @all_requests
        def catchall(url, req):
            self.assertIn("https://fhir.backend.bluebutton.hhsdevcloud.us/{}/fhir/Patient/".format(ver), req.url)
            self.assertIn("_format=application%2Fjson%2Bfhir", req.url)
            self.assertIn("_id=-20140000008325", req.url)
            self.assertIn("startIndex=0", req.url)
            self.assertIn("_count=5", req.url)
            self.assertNotIn("hello", req.url)
            self.assertEqual(expected_request['method'], req.method)
            self.assertDictContainsSubset(expected_request['headers'], req.headers)

            return {
                'status_code': 200,
                # TODO replace this with true backend response, this has been post proccessed
                'content': patient_response,
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_patient_search' if not v2 else 'bb_oauth_fhir_patient_search_v2'),
                {'count': 5, 'hello': 'world'},
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 200)
            # asserts no significant transformation
            self.assertEqual(response.json()['entry'], patient_response['entry'])
            self.assertTrue(len(response.json()['link']) > 0)
            self.assertIn("_count=5", response.json()['link'][0]['url'])

    def test_search_eob_by_parameters_request(self):
        self._search_eob_by_parameters_request(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
    def test_search_eob_by_parameters_request_v2(self):
        self._search_eob_by_parameters_request(True)

    def _search_eob_by_parameters_request(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')
        ver = 'v1' if not v2 else 'v2'

        @all_requests
        def catchall(url, req):
            self.assertIn("https://fhir.backend.bluebutton.hhsdevcloud.us/{}/fhir/ExplanationOfBenefit/".format(ver), req.url)
            self.assertIn("_format=application%2Fjson%2Bfhir", req.url)

            return {
                'status_code': 200,
                'content': {
                    'resourceType': 'ExplanationOfBenefit',
                    'patient': {
                        'reference': 'stuff/-20140000008325',
                    },
                },
            }

        # Test _lastUpdated with valid parameter starting with "lt"
        with HTTMock(catchall):
            response = self.client.get(
                reverse('bb_oauth_fhir_eob_search' if not v2 else 'bb_oauth_fhir_eob_search_v2'),
                {'_lastUpdated': 'lt2019-11-22T14:00:00-05:00'},
                Authorization="Bearer %s" % (first_access_token))
            self.assertEqual(response.status_code, 200)

        # Test _lastUpdated with invalid parameter starting with "zz"
        with HTTMock(catchall):
            response = self.client.get(
                reverse('bb_oauth_fhir_eob_search' if not v2 else 'bb_oauth_fhir_eob_search_v2'),
                {'_lastUpdated': 'zz2020-11-22T14:00:00-05:00'},
                Authorization="Bearer %s" % (first_access_token))

            content = json.loads(response.content.decode("utf-8"))
            self.assertEqual(content['detail'], 'the _lastUpdated operator is not valid')
            self.assertEqual(response.status_code, 400)

        # Test type= with single valid value: "pde"
        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_eob_search' if not v2 else 'bb_oauth_fhir_eob_search_v2'),
                {'type': 'pde'},
                Authorization="Bearer %s" % (first_access_token))
            self.assertEqual(response.status_code, 200)

        # Test type= with multiple (all valid values)
        with HTTMock(catchall):
            response = self.client.get(
                reverse('bb_oauth_fhir_eob_search' if not v2 else 'bb_oauth_fhir_eob_search_v2'),
                {'type': 'carrier,'
                         'pde,'
                         'dme,'
                         'hha,'
                         'hospice,'
                         'inpatient,'
                         'outpatient,'
                         'snf,'
                         'https://bluebutton.cms.gov/resources/codesystem/eob-type|carrier,'
                         'https://bluebutton.cms.gov/resources/codesystem/eob-type|pde,'
                         'https://bluebutton.cms.gov/resources/codesystem/eob-type|dme,'
                         'https://bluebutton.cms.gov/resources/codesystem/eob-type|hha,'
                         'https://bluebutton.cms.gov/resources/codesystem/eob-type|hospice,'
                         'https://bluebutton.cms.gov/resources/codesystem/eob-type|inpatient,'
                         'https://bluebutton.cms.gov/resources/codesystem/eob-type|outpatient,'
                         'https://bluebutton.cms.gov/resources/codesystem/eob-type|snf'},
                Authorization="Bearer %s" % (first_access_token))
            self.assertEqual(response.status_code, 200)

        # Test type= with an invalid type
        with HTTMock(catchall):
            response = self.client.get(
                reverse('bb_oauth_fhir_eob_search' if not v2 else 'bb_oauth_fhir_eob_search_v2'),
                {'type': 'carrier,'
                         'INVALID-TYPE,'
                         'dme,'},
                Authorization="Bearer %s" % (first_access_token))

            content = json.loads(response.content.decode("utf-8"))
            self.assertEqual(content['detail'], 'the type parameter value is not valid')
            self.assertEqual(response.status_code, 400)

    def test_read_request(self):
        self._read_patient_request(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
    def test_read_patient_request_v2(self):
        self._read_patient_request(True)

    def _read_patient_request(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')
        ver = 'v1' if not v2 else 'v2'
        expected_request = get_expected_read_request(ver)

        @all_requests
        def catchall(url, req):
            self.assertEqual(expected_request['url'], req.url)
            self.assertEqual(expected_request['method'], req.method)
            self.assertDictContainsSubset(expected_request['headers'], req.headers)

            return {
                'status_code': 200,
                'content':{"resourceType":"Patient","id":"-20140000008325","extension":[{"url":"https://bluebutton.cms.gov/resources/variables/race","valueCoding":{"system":"https://bluebutton.cms.gov/resources/variables/race","code":"1","display":"White"}}],"identifier":[{"system":"https://bluebutton.cms.gov/resources/variables/bene_id","value":"-20140000008325"},{"system":"https://bluebutton.cms.gov/resources/identifier/hicn-hash","value":"2025fbc612a884853f0c245e686780bf748e5652360ecd7430575491f4e018c5"}],"name":[{"use":"usual","family":"Doe","given":["Jane","X"]}],"gender":"unknown","birthDate":"2014-06-01","address":[{"district":"999","state":"15","postalCode":"99999"}]} # noqa
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_patient_read_or_update_or_delete'
                    if not v2 else 'bb_oauth_fhir_patient_read_or_update_or_delete_v2',
                    kwargs={'resource_id': '-20140000008325'}),
                {'hello': 'world'},
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 200)

    def test_read_eob_request(self):
        self._read_eob_request(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
    def test_read_eob_request_v2(self):
        self._read_eob_request(True)

    def _read_eob_request(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': {
                    'resourceType': 'ExplanationOfBenefit',
                    'patient': {
                        'reference': 'stuff/-20140000008325',
                    },
                },
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_eob_read_or_update_or_delete'
                    if not v2 else 'bb_oauth_fhir_eob_read_or_update_or_delete_v2',
                    kwargs={'resource_id': 'eob_id'}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 200)

    def test_read_coverage_request(self):
        self._read_coverage_request(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
    def test_read_coverage_request_v2(self):
        self._read_coverage_request(True)

    def _read_coverage_request(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': {
                    'resourceType': 'Coverage',
                    'beneficiary': {
                        'reference': 'stuff/-20140000008325',
                    },
                },
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_coverage_read_or_update_or_delete'
                    if not v2 else 'bb_oauth_fhir_coverage_read_or_update_or_delete_v2',
                    kwargs={'resource_id': 'coverage_id'}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 200)
