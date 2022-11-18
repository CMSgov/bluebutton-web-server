import json

from django.test.client import Client
from django.urls import reverse
from httmock import all_requests, HTTMock
from oauth2_provider.models import get_access_token_model

from apps.test import BaseApiTest

AccessToken = get_access_token_model()

C4BB_PROFILE_URLS = {
    "INPATIENT": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Inpatient-Institutional",
    "OUTPATIENT": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Outpatient-Institutional",
    "PHARMACY": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Pharmacy",
    "NONCLINICIAN": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Professional-NonClinician",
}

C4BB_SYSTEM_TYPES = {
    "IDTYPE": "http://hl7.org/fhir/us/carin-bb/CodeSystem/C4BBIdentifierType",
}


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

    def _assertHasC4BBProfile(self, resource, c4bb_profile, v2=False):
        meta_profile = None
        try:
            meta_profile = resource['meta']['profile'][0]
        except KeyError:
            pass
        if not v2:
            self.assertIsNone(meta_profile)
        else:
            self.assertIsNotNone(meta_profile)
            self.assertEqual(meta_profile, c4bb_profile)

    def _assertHasC4BBIdentifier(self, resource, c4bb_type, v2=False):
        identifiers = None

        try:
            identifiers = resource['identifier']
        except KeyError:
            pass

        self.assertIsNotNone(identifiers)

        hasC4BB = False

        for id in identifiers:
            try:
                system = id['type']['coding'][0]['system']
                if system == c4bb_type:
                    hasC4BB = True
                    break
            except KeyError:
                pass

        if v2:
            self.assertTrue(hasC4BB)
        else:
            self.assertFalse(hasC4BB)

    def test_read_patient_request(self):
        self._read_patient_request(False)

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
            self._assertHasC4BBIdentifier(response.json(), C4BB_SYSTEM_TYPES['IDTYPE'], v2)

    def test_search_patient_request(self):
        self._search_patient_request(False)

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
                self._assertHasC4BBIdentifier(r['resource'], C4BB_SYSTEM_TYPES['IDTYPE'], v2)

    def test_search_eob_by_parameters_request(self):
        self._search_eob_by_parameters_request(False)

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
                'content': get_response_json("eob_search_pt_{}".format(ver)),
            }

        # Test service-date with valid parameter starting with "lt"
        with HTTMock(catchall):
            response = self.client.get(
                reverse('bb_oauth_fhir_eob_search' if not v2 else 'bb_oauth_fhir_eob_search_v2'),
                {'service-date': 'lt2022-11-18'},
                Authorization="Bearer %s" % (first_access_token))
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob
            for r in response.json()['entry']:
                self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['PHARMACY'], v2)

        # Test service-date range with valid parameter starting with "lt" and "ge"
        # example url:
        # http://localhost:8000/v2/fhir/ExplanationOfBenefit?
        # _format=application%2Fjson%2Bfhir&startIndex=0
        # &_count=10&patient=-20000000000001
        # &service-date=gt2000-01-01
        # &service-date=le2022-11-18
        with HTTMock(catchall):
            search_url = reverse('bb_oauth_fhir_eob_search' if not v2 else 'bb_oauth_fhir_eob_search_v2')
            response = self.client.get(search_url + "?service-date=gt2000-01-01&service-date=le2022-11-18",
                                       Authorization="Bearer %s" % (first_access_token))
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob
            for r in response.json()['entry']:
                self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['PHARMACY'], v2)

        # Test service-date with invalid parameter starting with "dd"
        with HTTMock(catchall):
            response = self.client.get(
                reverse('bb_oauth_fhir_eob_search' if not v2 else 'bb_oauth_fhir_eob_search_v2'),
                {'service-date': 'dd2022-11-18'},
                Authorization="Bearer %s" % (first_access_token))

            content = json.loads(response.content.decode("utf-8"))
            self.assertEqual(content['detail'], 'the service-date operator is not valid')
            self.assertEqual(response.status_code, 400)

        # Test _lastUpdated with valid parameter starting with "lt"
        with HTTMock(catchall):
            response = self.client.get(
                reverse('bb_oauth_fhir_eob_search' if not v2 else 'bb_oauth_fhir_eob_search_v2'),
                {'_lastUpdated': 'lt2019-11-22T14:00:00-05:00'},
                Authorization="Bearer %s" % (first_access_token))
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob
            # noticed resources ids are different: in v1 the id is like: "id": "carrier--20587716665",
            # in v2: "id": "pde--3269834580",
            # will check resource id in the loop upon confirm with BFD
            for r in response.json()['entry']:
                self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['PHARMACY'], v2)

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
            # assert v1 and v2 eob
            for r in response.json()['entry']:
                self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['PHARMACY'], v2)

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
            # assert v1 and v2 eob
            for r in response.json()['entry']:
                self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['PHARMACY'], v2)

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

    def test_read_eob_request(self):
        self._read_eob_request(False)

    def test_read_eob_request_v2(self):
        self._read_eob_request(True)

    def _read_eob_request(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json("eob_read_carrier_{}".format('v2' if v2 else 'v1')),
            }

        with HTTMock(catchall):
            # here the eob carrier id serve as fake id
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_eob_read_or_update_or_delete'
                    if not v2 else 'bb_oauth_fhir_eob_read_or_update_or_delete_v2',
                    kwargs={'resource_id': 'carrier--22639159481'}),
                Authorization="Bearer %s" % (first_access_token))

            # assert v1 and v2 eob read using carrier id
            self._assertHasC4BBProfile(response.json(), C4BB_PROFILE_URLS['NONCLINICIAN'], v2)

    def test_read_eob_inpatient_request(self):
        self._read_eob_inpatient_request(False)

    def test_read_eob_inpatient_request_v2(self):
        self._read_eob_inpatient_request(True)

    def _read_eob_inpatient_request(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json("eob_read_in_pt_{}".format('v2' if v2 else 'v1')),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_eob_read_or_update_or_delete'
                    if not v2 else 'bb_oauth_fhir_eob_read_or_update_or_delete_v2',
                    kwargs={'resource_id': 'inpatient-4436342082'}),
                Authorization="Bearer %s" % (first_access_token))
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob inpatient
            self._assertHasC4BBProfile(response.json(), C4BB_PROFILE_URLS['INPATIENT'], v2)

    def test_read_eob_outpatient_request(self):
        self._read_eob_outpatient_request(False)

    def test_read_eob_outpatient_request_v2(self):
        self._read_eob_outpatient_request(True)

    def _read_eob_outpatient_request(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json("eob_read_out_pt_{}".format('v2' if v2 else 'v1')),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_eob_read_or_update_or_delete'
                    if not v2 else 'bb_oauth_fhir_eob_read_or_update_or_delete_v2',
                    kwargs={'resource_id': 'outpatient-4388491497'}),
                Authorization="Bearer %s" % (first_access_token))
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob outpatient
            self._assertHasC4BBProfile(response.json(), C4BB_PROFILE_URLS['OUTPATIENT'], v2)

    def test_read_coverage_request(self):
        self._read_coverage_request(False)

    def test_read_coverage_request_v2(self):
        self._read_coverage_request(True)

    def _read_coverage_request(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            return {'status_code': 200,
                    'content': get_response_json("coverage_read_{}".format('v2' if v2 else 'v1')), }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_coverage_read_or_update_or_delete'
                    if not v2 else 'bb_oauth_fhir_coverage_read_or_update_or_delete_v2',
                    kwargs={'resource_id': 'coverage_id'}),
                Authorization="Bearer %s" % (first_access_token))
            self.assertEqual(response.status_code, 200)
            subId = None
            relationship = None
            try:
                subId = response.json()['subscriberId']
            except KeyError:
                pass
            try:
                relationship = response.json()['relationship']
            except KeyError:
                pass
            if not v2:
                self.assertIsNone(subId)
                self.assertIsNone(relationship)
            else:
                self.assertIsNotNone(subId)
                self.assertIsNotNone(relationship)

    def test_search_coverage_request(self):
        self._search_coverage_request(False)

    def test_search_coverage_request_v2(self):
        self._search_coverage_request(True)

    def _search_coverage_request(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            return {'status_code': 200,
                    'content': get_response_json("coverage_search_{}".format('v2' if v2 else 'v1')), }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_coverage_search'
                    if not v2 else 'bb_oauth_fhir_coverage_search_v2'),
                Authorization="Bearer %s" % (first_access_token))
            self.assertEqual(response.status_code, 200)

            # assert v1 and v2 coverage resources
            for r in response.json()['entry']:
                subId = None
                relationship = None
                try:
                    subId = r['resource']['subscriberId']
                except KeyError:
                    pass
                try:
                    relationship = r['resource']['relationship']
                except KeyError:
                    pass
                if not v2:
                    self.assertIsNone(subId)
                    self.assertIsNone(relationship)
                else:
                    self.assertIsNotNone(subId)
                    self.assertIsNotNone(relationship)

    def test_fhir_meta_request(self):
        self._query_fhir_meta(False)

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

    def test_userinfo_request(self):
        self._query_userinfo(False)

    def test_userinfo_request_v2(self):
        self._query_userinfo(True)

    def _query_userinfo(self, v2=False):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json("userinfo_{}".format('v2' if v2 else 'v1')),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'openid_connect_userinfo'
                    if not v2 else 'openid_connect_userinfo_v2',),
                Authorization="Bearer %s" % (first_access_token))
            # identical response for v1 and v2
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["sub"], response.json()["patient"])

    def test_err_response_caused_by_illegalarguments(self):
        self._err_response_caused_by_illegalarguments(False)

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
