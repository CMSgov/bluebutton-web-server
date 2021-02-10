import json

from django.test.client import Client
from django.urls import reverse
from httmock import all_requests, HTTMock
from oauth2_provider.models import get_access_token_model
from waffle.testutils import override_switch, override_flag

from apps.test import BaseApiTest

AccessToken = get_access_token_model()


def get_response_json(resource_file_name):
    response_file = open("./apps/fhir/bluebutton/tests/fhir_resources/{}.json".format(resource_file_name), 'r')
    resource = json.load(response_file)
    response_file.close()
    return resource


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

        @all_requests
        def catchall(url, req):

            return {
                'status_code': 200,
                'content': get_response_json("patient_search_{}".format(ver)),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_patient_search' if not v2 else 'bb_oauth_fhir_patient_search_v2'),
                {'count': 5, 'hello': 'world'},
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 200)
            # check C4BB in resource as v2 charactor
            self.assertIsNotNone(response.json()['entry'])
            self.assertTrue(len(response.json()['link']) > 0)
            for r in response.json()['entry']:
                self.assertEqual(r['resource']['resourceType'], "Patient")

                identifiers = None

                try:
                    identifiers = r['resource']['identifier']
                except KeyError:
                    pass

                self.assertIsNotNone(identifiers)

                hasC4BB = False

                for id in identifiers:
                    try:
                        system = id['type']['coding'][0]['system']
                        if system == "http://hl7.org/fhir/us/carin-bb/CodeSystem/C4BBIdentifierType":
                            hasC4BB = True
                            break
                    except KeyError:
                        pass

                if v2:
                    self.assertTrue(hasC4BB)
                else:
                    self.assertFalse(hasC4BB)

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

    def test_read_patient_request(self):
        self._read_patient_request(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
    def test_read_patient_request_v2(self):
        self._read_patient_request(True)

    def _read_patient_request(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):

            return {
                'status_code': 200,
                'content': get_response_json("patient_read_{}".format('v2' if v2 else 'v1')),
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
            identifiers = None

            try:
                identifiers = response.json()['identifier']
            except KeyError:
                pass

            self.assertIsNotNone(identifiers)

            hasC4BB = False

            for id in identifiers:
                try:
                    system = id['type']['coding'][0]['system']
                    if system == "http://hl7.org/fhir/us/carin-bb/CodeSystem/C4BBIdentifierType":
                        hasC4BB = True
                        break
                except KeyError:
                    pass

            if v2:
                self.assertTrue(hasC4BB)
            else:
                self.assertFalse(hasC4BB)

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

    def test_fhir_meta_request(self):
        self._query_fhir_meta(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
    def test_fhir_meta_request_v2(self):
        self._query_fhir_meta(True)

    def _query_fhir_meta(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json("fhir_meta_{}".format('v2' if v2 else 'v1')),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'fhir_conformance_metadata'
                    if not v2 else 'fhir_conformance_metadata_v2',),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["resourceType"], "CapabilityStatement")
            self.assertEqual(response.json()["fhirVersion"], '4.0.0' if v2 else '3.0.2')

    def test_err_response_caused_by_illegalarguments(self):
        self._err_response_caused_by_illegalarguments(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
    def test_err_response_caused_by_illegalarguments_v2(self):
        self._err_response_caused_by_illegalarguments(True)

    def _err_response_caused_by_illegalarguments(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):

            return {
                'status_code': 500,
                'content': get_response_json("resource_error_response"),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_patient_read_or_update_or_delete'
                    if not v2 else 'bb_oauth_fhir_patient_read_or_update_or_delete_v2',
                    kwargs={'resource_id': '-20140000008325'}),
                {'hello': 'world'},
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 400)
