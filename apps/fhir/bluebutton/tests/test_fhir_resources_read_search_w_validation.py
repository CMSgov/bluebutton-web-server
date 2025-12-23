import json

from django.conf import settings
from django.test.client import Client
from django.urls import reverse
from apps.versions import Versions
from httmock import all_requests, HTTMock
from http import HTTPStatus
from oauth2_provider.models import get_access_token_model
from waffle.testutils import override_switch

from apps.test import BaseApiTest

from hhs_oauth_server.settings.base import FHIR_SERVER

AccessToken = get_access_token_model()

C4BB_PROFILE_URLS = {
    'INPATIENT': 'http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Inpatient-Institutional',
    'OUTPATIENT': 'http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Outpatient-Institutional',
    'PHARMACY': 'http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Pharmacy',
    'NONCLINICIAN': 'http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Professional-NonClinician',
}

C4BB_SYSTEM_TYPES = {
    'IDTYPE': 'http://hl7.org/fhir/us/carin-bb/CodeSystem/C4BBIdentifierType',
}

FHIR_ID_V2 = settings.DEFAULT_SAMPLE_FHIR_ID_V2
FHIR_ID_V3 = settings.DEFAULT_SAMPLE_FHIR_ID_V3
BAD_PARAMS_ACCEPTABLE_VERSIONS = [Versions.V1, Versions.V2]

read_update_delete_patient_urls = {
    1: 'bb_oauth_fhir_patient_read_or_update_or_delete',
    2: 'bb_oauth_fhir_patient_read_or_update_or_delete_v2',
    3: 'bb_oauth_fhir_patient_read_or_update_or_delete_v3'
}

read_update_delete_eob_urls = {
    1: 'bb_oauth_fhir_eob_read_or_update_or_delete',
    2: 'bb_oauth_fhir_eob_read_or_update_or_delete_v2',
    3: 'bb_oauth_fhir_eob_read_or_update_or_delete_v3'
}

read_update_delete_coverage_urls = {
    1: 'bb_oauth_fhir_coverage_read_or_update_or_delete',
    2: 'bb_oauth_fhir_coverage_read_or_update_or_delete_v2',
    3: 'bb_oauth_fhir_coverage_read_or_update_or_delete_v3'
}

search_patient_urls = {
    1: 'bb_oauth_fhir_patient_search',
    2: 'bb_oauth_fhir_patient_search_v2',
    3: 'bb_oauth_fhir_patient_search_v3'
}

search_eob_urls = {
    1: 'bb_oauth_fhir_eob_search',
    2: 'bb_oauth_fhir_eob_search_v2',
    3: 'bb_oauth_fhir_eob_search_v3'
}

search_coverage_urls = {
    1: 'bb_oauth_fhir_coverage_search',
    2: 'bb_oauth_fhir_coverage_search_v2',
    3: 'bb_oauth_fhir_coverage_search_v3'
}

userinfo_urls = {
    1: 'openid_connect_userinfo',
    2: 'openid_connect_userinfo_v2',
    3: 'openid_connect_userinfo_v3',
}

fhir_conformance_urls = {
    1: 'fhir_conformance_metadata',
    2: 'fhir_conformance_metadata_v2',
    3: 'fhir_conformance_metadata_v3',
}


def get_response_json(resource_file_name):
    response_file = open(f'./apps/fhir/bluebutton/tests/fhir_resources/{resource_file_name}.json')
    resource = json.load(response_file)
    response_file.close()
    return resource


class FHIRResourcesReadSearchTest(BaseApiTest):

    def setUp(self):
        # create read and write capabilities
        self.read_capability = self._create_capability('Read', [])
        self.write_capability = self._create_capability('Write', [])
        self._create_capability('patient', [
            ['GET', r'\/v1\/fhir\/Patient\/\-\d+'],
            ['GET', r'\/v1\/fhir\/Patient\/\d+'],
            ['GET', '/v1/fhir/Patient'],
        ])
        self._create_capability('coverage', [
            ['GET', r'\/v1\/fhir\/Coverage\/.+'],
            ['GET', '/v1/fhir/Coverage'],
        ])
        self._create_capability('eob', [
            ['GET', r'\/v1\/fhir\/ExplanationOfBenefit\/.+'],
            ['GET', '/v1/fhir/ExplanationOfBenefit'],
        ])
        # Setup the RequestFactory
        self.client = Client()

    def _assertHasC4BBProfile(self, resource, c4bb_profile, version=1):
        meta_profile = None
        try:
            meta_profile = resource['meta']['profile'][0]
        except KeyError:
            pass
        if version == 1:
            self.assertIsNone(meta_profile)
        else:
            self.assertIsNotNone(meta_profile)
            self.assertEqual(meta_profile, c4bb_profile)

    def _assertHasC4BBIdentifier(self, resource, c4bb_type, version=1):
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

        if version >= 2:
            self.assertTrue(hasC4BB)
        else:
            self.assertFalse(hasC4BB)

    def test_read_patient_request(self):
        self._read_patient_request(1)

    def test_read_patient_request_v2(self):
        self._read_patient_request(2)

    def _read_patient_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)

        @all_requests
        def catchall(url, req):

            return {
                'status_code': 200,
                'content': get_response_json(f'patient_read_v{version}'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(read_update_delete_patient_urls[version],
                        kwargs={'resource_id': '-20140000008325'}),
                Authorization='Bearer %s' % (first_access_token))

            self.assertEqual(response.status_code, 200)
            self._assertHasC4BBIdentifier(response.json(), C4BB_SYSTEM_TYPES['IDTYPE'], version)

    def test_search_patient_request(self):
        self._search_patient_request(1)

    def test_search_patient_request_v2(self):
        self._search_patient_request(2)

    def _search_patient_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/Patient.read'
        ac.save()

        @all_requests
        def catchall(url, req):

            return {
                'status_code': 200,
                'content': get_response_json(f'patient_search_v{version}'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(search_patient_urls[version]),
                {'count': 5},
                Authorization='Bearer %s' % (first_access_token))

            self.assertEqual(response.status_code, 200)
            # check C4BB in resource as v2 charactor
            self.assertIsNotNone(response.json()['entry'])
            self.assertTrue(len(response.json()['link']) > 0)
            for r in response.json()['entry']:
                self._assertHasC4BBIdentifier(r['resource'], C4BB_SYSTEM_TYPES['IDTYPE'], version)

    @override_switch('v3_endpoints', active=True)
    def test_search_eob_by_parameter_tag(self):
        self._search_eob_by_parameter_tag(1)

    @override_switch('v3_endpoints', active=True)
    def test_search_eob_by_parameter_tag_v2(self):
        self._search_eob_by_parameter_tag(2)

    @override_switch('v3_endpoints', active=True)
    def _search_eob_by_parameter_tag(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/ExplanationOfBenefit.read'
        ac.save()

        @all_requests
        def catchall_w_tag_qparam(url, req):
            # this is called in case EOB search with good tag
            self.assertIn(f'{FHIR_SERVER["FHIR_URL"]}/v{version}/fhir/ExplanationOfBenefit/', req.url)
            self.assertIn('_format=application%2Ffhir%2Bjson', req.url)
            # parameters encoded in prepared request's body
            self.assertTrue(('_tag=Adjudicated' in req.url) or ('_tag=PartiallyAdjudicated' in req.url))

            return {
                'status_code': 200,
                'content': get_response_json(f'eob_search_pt_v{version}'),
            }

        @all_requests
        def catchall(url, req):
            self.assertIn(f'{FHIR_SERVER["FHIR_URL"]}/v{version}/fhir/ExplanationOfBenefit/', req.url)
            self.assertIn('_format=application%2Ffhir%2Bjson', req.url)

            return {
                'status_code': 200,
                'content': get_response_json(f'eob_search_pt_v{version}'),
            }
        # Test _tag with valid parameter value e.g. Adjudicated, PartiallyAdjudicated
        with HTTMock(catchall_w_tag_qparam):
            response = self.client.get(
                reverse(search_eob_urls[version]),
                {'_tag': 'Adjudicated'},
                Authorization='Bearer %s' % (first_access_token))
            # just check for 200 is sufficient
            self.assertEqual(response.status_code, 200)

        # Test _tag with invalid parameter value e.g.: Adjudiacted-Typo
        with HTTMock(catchall):
            response = self.client.get(
                reverse(search_eob_urls[version]),
                {'_tag': 'Adjudiacted-Typo'},
                Authorization='Bearer %s' % (first_access_token))

            content = json.loads(response.content.decode('utf-8'))
            self.assertTrue(content['detail'].startswith('Invalid _tag value ('))
            self.assertTrue(content['detail'].endswith("'PartiallyAdjudicated' or 'Adjudicated' expected."))
            self.assertTrue('Adjudiacted-Typo' in content['detail'])
            self.assertEqual(response.status_code, 400)

    def test_search_eob_by_parameters_request(self):
        self._search_eob_by_parameters_request(1)

    def test_search_eob_by_parameters_request_v2(self):
        self._search_eob_by_parameters_request(2)

    def _search_eob_by_parameters_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/ExplanationOfBenefit.read'
        ac.save()

        @all_requests
        def catchall(url, req):
            self.assertIn(f'{FHIR_SERVER["FHIR_URL"]}/v{version}/fhir/ExplanationOfBenefit/', req.url)
            self.assertIn('_format=application%2Ffhir%2Bjson', req.url)

            return {
                'status_code': 200,
                'content': get_response_json(f'eob_search_pt_v{version}'),
            }

        # Test service-date with valid parameter starting with 'lt'
        with HTTMock(catchall):
            response = self.client.get(
                reverse(search_eob_urls[version]),
                {'service-date': 'lt2022-11-18'},
                Authorization='Bearer %s' % (first_access_token))
            self.assertEqual(response.status_code, 200)
            for r in response.json()['entry']:
                self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['PHARMACY'], version)

        # Test service-date range with valid parameter starting with 'lt' and 'ge'
        # example url:
        # http://localhost:8000/v2/fhir/ExplanationOfBenefit?
        # _format=application%2Fjson%2Bfhir&startIndex=0
        # &_count=10&patient=-20000000000001
        # &service-date=gt2000-01-01
        # &service-date=le2022-11-18
        with HTTMock(catchall):
            search_url = reverse(search_eob_urls[version])
            response = self.client.get(search_url + '?service-date=gt2000-01-01&service-date=le2022-11-18',
                                       Authorization='Bearer %s' % (first_access_token))
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob
            for r in response.json()['entry']:
                self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['PHARMACY'], version)

        # Test service-date with invalid parameter starting with 'dd'
        with HTTMock(catchall):
            response = self.client.get(
                reverse(search_eob_urls[version]),
                {'service-date': 'dd2022-11-18'},
                Authorization='Bearer %s' % (first_access_token))

            content = json.loads(response.content.decode('utf-8'))
            self.assertEqual(content['detail'], 'the service-date operator is not valid')
            self.assertEqual(response.status_code, 400)

        # Test _lastUpdated with valid parameter starting with 'lt'
        with HTTMock(catchall):
            response = self.client.get(
                reverse(search_eob_urls[version]),
                {'_lastUpdated': 'lt2019-11-22T14:00:00-05:00'},
                Authorization='Bearer %s' % (first_access_token))
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob
            # noticed resources ids are different: in v1 the id is like: 'id': 'carrier--20587716665',
            # in v2: 'id': 'pde--3269834580',
            # will check resource id in the loop upon confirm with BFD
            for r in response.json()['entry']:
                self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['PHARMACY'], version)

        # Test _lastUpdated with invalid parameter starting with 'zz'
        with HTTMock(catchall):
            response = self.client.get(
                reverse(search_eob_urls[version]),
                {'_lastUpdated': 'zz2020-11-22T14:00:00-05:00'},
                Authorization='Bearer %s' % (first_access_token))

            content = json.loads(response.content.decode('utf-8'))
            self.assertEqual(content['detail'], 'the _lastUpdated operator is not valid')
            self.assertEqual(response.status_code, 400)

        # Test type= with single valid value: 'pde'
        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    search_eob_urls[version]),
                {'type': 'pde'},
                Authorization='Bearer %s' % (first_access_token))
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob
            for r in response.json()['entry']:
                self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['PHARMACY'], version)

        # Test type= with multiple (all valid values)
        with HTTMock(catchall):
            response = self.client.get(
                reverse(search_eob_urls[version]),
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
                Authorization='Bearer %s' % (first_access_token))
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob
            for r in response.json()['entry']:
                self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['PHARMACY'], version)

        # Test type= with an invalid type
        with HTTMock(catchall):
            response = self.client.get(
                reverse(search_eob_urls[version]),
                {'type': 'carrier,'
                         'INVALID-TYPE,'
                         'dme,'},
                Authorization='Bearer %s' % (first_access_token))

            content = json.loads(response.content.decode('utf-8'))
            self.assertEqual(content['detail'], 'the type parameter value is not valid')
            self.assertEqual(response.status_code, 400)

    def test_read_eob_request(self):
        self._read_eob_request(1)

    def test_read_eob_request_v2(self):
        self._read_eob_request(2)

    def _read_eob_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json(f'eob_read_carrier_v{version}'),
            }

        with HTTMock(catchall):
            # here the eob carrier id serve as fake id
            response = self.client.get(
                reverse(read_update_delete_eob_urls[version],
                        kwargs={'resource_id': 'carrier--22639159481'}),
                Authorization='Bearer %s' % (first_access_token))

            # assert v1 and v2 eob read using carrier id
            self._assertHasC4BBProfile(response.json(), C4BB_PROFILE_URLS['NONCLINICIAN'], version)

    def test_read_eob_inpatient_request(self):
        self._read_eob_inpatient_request(1)

    def test_read_eob_inpatient_request_v2(self):
        self._read_eob_inpatient_request(2)

    def _read_eob_inpatient_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json(f'eob_read_in_pt_v{version}'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(read_update_delete_eob_urls[version],
                        kwargs={'resource_id': 'inpatient-4436342082'}),
                Authorization='Bearer %s' % (first_access_token))
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob inpatient
            self._assertHasC4BBProfile(response.json(), C4BB_PROFILE_URLS['INPATIENT'], version)

    def test_read_eob_outpatient_request(self):
        self._read_eob_outpatient_request(1)

    def test_read_eob_outpatient_request_v2(self):
        self._read_eob_outpatient_request(2)

    def _read_eob_outpatient_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json(f'eob_read_out_pt_v{version}'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(read_update_delete_eob_urls[version],
                        kwargs={'resource_id': 'outpatient-4388491497'}),
                Authorization='Bearer %s' % (first_access_token))
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob outpatient
            self._assertHasC4BBProfile(response.json(), C4BB_PROFILE_URLS['OUTPATIENT'], version)

    def test_read_coverage_request(self):
        self._read_coverage_request(1)

    def test_read_coverage_request_v2(self):
        self._read_coverage_request(2)

    def _read_coverage_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)

        @all_requests
        def catchall(url, req):
            return {'status_code': 200,
                    'content': get_response_json(f'coverage_read_v{version}'), }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(read_update_delete_coverage_urls[version],
                        kwargs={'resource_id': 'coverage_id'}),
                Authorization='Bearer %s' % (first_access_token))
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
            if version == 1:
                self.assertIsNone(subId)
                self.assertIsNone(relationship)
            else:
                self.assertIsNotNone(subId)
                self.assertIsNotNone(relationship)

    def test_search_coverage_request(self):
        self._search_coverage_request(1)

    def test_search_coverage_request_v2(self):
        self._search_coverage_request(2)

    def _search_coverage_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/Coverage.read'
        ac.save()

        @all_requests
        def catchall(url, req):
            return {'status_code': 200,
                    'content': get_response_json(f'coverage_search_v{version}')}

        with HTTMock(catchall):
            response = self.client.get(
                reverse(search_coverage_urls[version]),
                Authorization='Bearer %s' % (first_access_token))
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
                if version == 1:
                    self.assertIsNone(subId)
                    self.assertIsNone(relationship)
                else:
                    self.assertIsNotNone(subId)
                    self.assertIsNotNone(relationship)

    def test_fhir_meta_request(self):
        self._query_fhir_meta(1)

    def test_fhir_meta_request_v2(self):
        self._query_fhir_meta(2)

    def _query_fhir_meta(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json(f'fhir_meta_v{version}'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(fhir_conformance_urls[version]),
                Authorization='Bearer %s' % (first_access_token))

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['resourceType'], 'CapabilityStatement')
            self.assertEqual(response.json()['fhirVersion'], '4.0.0' if version >= 2 else '3.0.2')

    def test_userinfo_request(self):
        self._query_userinfo(1)

    def test_userinfo_request_v2(self):
        self._query_userinfo(2)

    def _query_userinfo(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json(f'userinfo_v{version}'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(userinfo_urls[version]),
                Authorization='Bearer %s' % (first_access_token))
            # identical response for v1 and v2
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['sub'], response.json()['patient'])

    def test_err_response_status_will_return_400_for_40x(self):
        # 401 will also return 400
        self._err_response_caused_by_illegalarguments(2, 401)

    def test_err_response_404_will_return_4o4(self):
        self._err_response_caused_by_illegalarguments(2, 404, 404)

    def test_err_response_500_will_return_502(self):
        self._err_response_caused_by_illegalarguments(2, 500, 502)

    def _err_response_caused_by_illegalarguments(self, version=1, bfd_status_code=500, expected_code=400):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2)

        @all_requests
        def catchall(url, req):

            return {
                'status_code': bfd_status_code,
                'content': get_response_json('resource_error_response'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(read_update_delete_patient_urls[version],
                        kwargs={'resource_id': '-20140000008325'}),
                Authorization='Bearer %s' % (first_access_token))

            self.assertEqual(response.status_code, expected_code)

    def test_eob_request_when_thrown_when_invalid_parameters_included_v1_and_v2(self) -> None:
        for version in BAD_PARAMS_ACCEPTABLE_VERSIONS:
            url = search_eob_urls[version]
            self._test_request_when_invalid_parameters_included(url, version, HTTPStatus.OK)

    def test_coverage_request_when_thrown_when_invalid_parameters_included_v1_and_v2(self) -> None:
        for version in BAD_PARAMS_ACCEPTABLE_VERSIONS:
            url = search_coverage_urls[version]
            self._test_request_when_invalid_parameters_included(url, version, HTTPStatus.OK)

    def test_patient_request_when_thrown_when_invalid_parameters_included_v1_and_v2(self) -> None:
        for version in BAD_PARAMS_ACCEPTABLE_VERSIONS:
            url = search_patient_urls[version]
            self._test_request_when_invalid_parameters_included(url, version, HTTPStatus.OK)

    def test_eob_request_when_thrown_when_invalid_parameters_included_v3(self) -> None:
        url = search_eob_urls[Versions.V3]
        self._test_request_when_invalid_parameters_included(url, Versions.V3, HTTPStatus.BAD_REQUEST)

    def test_coverage_request_when_thrown_when_invalid_parameters_included_v3(self) -> None:
        url = search_coverage_urls[Versions.V3]
        self._test_request_when_invalid_parameters_included(url, Versions.V3, HTTPStatus.BAD_REQUEST)

    def test_patient_request_when_thrown_when_invalid_parameters_included_v3(self) -> None:
        url = search_patient_urls[Versions.V3]
        self._test_request_when_invalid_parameters_included(url, Versions.V3, HTTPStatus.BAD_REQUEST)

    @override_switch('v3_endpoints', active=True)
    def _test_request_when_invalid_parameters_included(self, url: str, version: int, expected_response_code: HTTPStatus) -> None:
        """Ensure that a 400 is thrown for each type of resource call when invalid parameters are included for v3
        And that it is a 200 response when it is v1 or v2

        Args:
            url (str): The url that will be called in the test
            expected_bad_params (List[str]): The bad parameters that cause the 400 error to be thrown
        """
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=FHIR_ID_V2, fhir_id_v3=FHIR_ID_V3)
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/Coverage.search patient/Patient.search patient/ExplanationOfBenefit.search'
        ac.save()

        response = self.client.get(
            reverse(url),
            {'hello': 'world'},
            Authorization='Bearer %s' % (first_access_token)
        )
        self.assertEqual(response.status_code, expected_response_code)
        if version == Versions.V3:
            self.assertEqual(response.json()['error'], 'Invalid parameters: [\'hello\']')
