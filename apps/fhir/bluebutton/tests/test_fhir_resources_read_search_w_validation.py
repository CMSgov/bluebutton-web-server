import json
from http import HTTPStatus

import pytest
from django.test.client import Client
from django.urls import reverse
from httmock import HTTMock, all_requests
from oauth2_provider.models import get_access_token_model
from waffle.testutils import override_switch

from apps.constants import (
    APPLICATION_DOES_NOT_HAVE_VALID_SCOPES,
    C4BB_PROFILE_URLS,
    COVERAGE_SCOPE,
    DEFAULT_SAMPLE_FHIR_ID_V2,
    DEFAULT_SAMPLE_FHIR_ID_V3,
    EOB_SCOPE,
    PATIENT_SCOPE,
)
from apps.dot_ext.models import AccessTokenExtension, Application, ProtectedCapability
from apps.fhir.constants import (
    BAD_PARAMS_ACCEPTABLE_VERSIONS,
    C4BB_SYSTEM_TYPES,
    DEFAULT_EOB_SOURCE,
    ENFORCE_PARAM_VALIDATION,
    EXCLUDE_SAMHSA_PARAMETER_VALUE,
    FHIR_CONFORMANCE_URLS,
    READ_UPDATE_DELETE_COVERAGE_URLS,
    READ_UPDATE_DELETE_EOB_URLS,
    READ_UPDATE_DELETE_PATIENT_URLS,
    SEARCH_COVERAGE_URLS,
    SEARCH_EOB_URLS,
    SEARCH_PATIENT_URLS,
    USERINFO_URLS,
)
from apps.test import BaseApiTest
from apps.versions import Versions
from hhs_oauth_server.settings.base import FHIR_SERVER

AccessToken = get_access_token_model()


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
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        @all_requests
        def catchall(url, req):

            return {
                'status_code': 200,
                'content': get_response_json(f'patient_read_v{version}'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(READ_UPDATE_DELETE_PATIENT_URLS[version], kwargs={'resource_id': DEFAULT_SAMPLE_FHIR_ID_V2}),
                Authorization='Bearer %s' % (first_access_token),
            )

            self.assertEqual(response.status_code, 200)
            self._assertHasC4BBIdentifier(response.json(), C4BB_SYSTEM_TYPES['IDTYPE'], version)

    def test_search_patient_request(self):
        self._search_patient_request(1)

    def test_search_patient_request_v2(self):
        self._search_patient_request(2)

    def _search_patient_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)
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
                reverse(SEARCH_PATIENT_URLS[version]), {'count': 5}, Authorization='Bearer %s' % (first_access_token)
            )

            self.assertEqual(response.status_code, 200)
            # check C4BB in resource as v2 character
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
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)
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

        # Test _tag with valid parameter value
        with HTTMock(catchall):
            response = self.client.get(
                reverse(SEARCH_EOB_URLS[version]),
                {'_tag': 'https://bluebutton.cms.gov/fhir/CodeSystem/System-Type|NationalClaimsHistory'},
                Authorization='Bearer %s' % (first_access_token),
            )
            # just check for 200 is sufficient
            self.assertEqual(response.status_code, 200)

    def test_search_eob_by_parameters_request(self):
        self._search_eob_by_parameters_request(1)

    def test_search_eob_by_parameters_request_v2(self):
        self._search_eob_by_parameters_request(2)

    def _search_eob_by_parameters_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)
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
                reverse(SEARCH_EOB_URLS[version]),
                {'service-date': 'lt2022-11-18'},
                Authorization='Bearer %s' % (first_access_token),
            )
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
            search_url = reverse(SEARCH_EOB_URLS[version])
            response = self.client.get(
                search_url + '?service-date=gt2000-01-01&service-date=le2022-11-18',
                Authorization='Bearer %s' % (first_access_token),
            )
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob
            for r in response.json()['entry']:
                self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['PHARMACY'], version)

        # Test service-date with invalid parameter starting with 'dd'
        with HTTMock(catchall):
            response = self.client.get(
                reverse(SEARCH_EOB_URLS[version]),
                {'service-date': 'dd2022-11-18'},
                Authorization='Bearer %s' % (first_access_token),
            )

            content = json.loads(response.content.decode('utf-8'))
            self.assertEqual(content['detail'], 'the service-date operator is not valid')
            self.assertEqual(response.status_code, 400)

        # Test _lastUpdated with valid parameter starting with 'lt'
        with HTTMock(catchall):
            response = self.client.get(
                reverse(SEARCH_EOB_URLS[version]),
                {'_lastUpdated': 'lt2019-11-22T14:00:00-05:00'},
                Authorization='Bearer %s' % (first_access_token),
            )
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
                reverse(SEARCH_EOB_URLS[version]),
                {'_lastUpdated': 'zz2020-11-22T14:00:00-05:00'},
                Authorization='Bearer %s' % (first_access_token),
            )

            content = json.loads(response.content.decode('utf-8'))
            self.assertEqual(content['detail'], 'the _lastUpdated operator is not valid')
            self.assertEqual(response.status_code, 400)

        # Test type= with single valid value: 'pde'
        with HTTMock(catchall):
            response = self.client.get(
                reverse(SEARCH_EOB_URLS[version]), {'type': 'pde'}, Authorization='Bearer %s' % (first_access_token)
            )
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob
            for r in response.json()['entry']:
                self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['PHARMACY'], version)

        # Test type= with multiple (all valid values)
        with HTTMock(catchall):
            response = self.client.get(
                reverse(SEARCH_EOB_URLS[version]),
                {
                    'type': 'carrier,'
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
                    'https://bluebutton.cms.gov/resources/codesystem/eob-type|snf'
                },
                Authorization='Bearer %s' % (first_access_token),
            )
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob
            for r in response.json()['entry']:
                self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['PHARMACY'], version)

        # Test type= with an invalid type
        with HTTMock(catchall):
            response = self.client.get(
                reverse(SEARCH_EOB_URLS[version]),
                {'type': 'carrier,INVALID-TYPE,dme,'},
                Authorization='Bearer %s' % (first_access_token),
            )

            content = json.loads(response.content.decode('utf-8'))
            self.assertEqual(content['detail'], 'the type parameter value is not valid')
            self.assertEqual(response.status_code, 400)

    def test_read_eob_request(self):
        self._read_eob_request(1)

    def test_read_eob_request_v2(self):
        self._read_eob_request(2)

    def _read_eob_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json(f'eob_read_carrier_v{version}'),
            }

        with HTTMock(catchall):
            # here the eob carrier id serve as fake id
            response = self.client.get(
                reverse(READ_UPDATE_DELETE_EOB_URLS[version], kwargs={'resource_id': 'carrier--22639159481'}),
                Authorization='Bearer %s' % (first_access_token),
            )

            # assert v1 and v2 eob read using carrier id
            self._assertHasC4BBProfile(response.json(), C4BB_PROFILE_URLS['NONCLINICIAN'], version)

    def test_read_eob_inpatient_request(self):
        self._read_eob_inpatient_request(1)

    def test_read_eob_inpatient_request_v2(self):
        self._read_eob_inpatient_request(2)

    def _read_eob_inpatient_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json(f'eob_read_in_pt_v{version}'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(READ_UPDATE_DELETE_EOB_URLS[version], kwargs={'resource_id': 'inpatient-4436342082'}),
                Authorization='Bearer %s' % (first_access_token),
            )
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob inpatient
            self._assertHasC4BBProfile(response.json(), C4BB_PROFILE_URLS['INPATIENT'], version)

    def test_read_eob_outpatient_request(self):
        self._read_eob_outpatient_request(1)

    def test_read_eob_outpatient_request_v2(self):
        self._read_eob_outpatient_request(2)

    def _read_eob_outpatient_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json(f'eob_read_out_pt_v{version}'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(READ_UPDATE_DELETE_EOB_URLS[version], kwargs={'resource_id': 'outpatient-4388491497'}),
                Authorization='Bearer %s' % (first_access_token),
            )
            self.assertEqual(response.status_code, 200)
            # assert v1 and v2 eob outpatient
            self._assertHasC4BBProfile(response.json(), C4BB_PROFILE_URLS['OUTPATIENT'], version)

    def test_read_coverage_request(self):
        self._read_coverage_request(1)

    def test_read_coverage_request_v2(self):
        self._read_coverage_request(2)

    def _read_coverage_request(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json(f'coverage_read_v{version}'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(READ_UPDATE_DELETE_COVERAGE_URLS[version], kwargs={'resource_id': 'coverage_id'}),
                Authorization='Bearer %s' % (first_access_token),
            )
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
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/Coverage.read'
        ac.save()

        @all_requests
        def catchall(url, req):
            return {'status_code': 200, 'content': get_response_json(f'coverage_search_v{version}')}

        with HTTMock(catchall):
            response = self.client.get(
                reverse(SEARCH_COVERAGE_URLS[version]), Authorization='Bearer %s' % (first_access_token)
            )
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
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json(f'fhir_meta_v{version}'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(FHIR_CONFORMANCE_URLS[version]), Authorization='Bearer %s' % (first_access_token)
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['resourceType'], 'CapabilityStatement')
            self.assertEqual(response.json()['fhirVersion'], '4.0.0' if version >= 2 else '3.0.2')

    def test_userinfo_request(self):
        self._query_userinfo(1)

    def test_userinfo_request_v2(self):
        self._query_userinfo(2)

    def _query_userinfo(self, version=1):
        # create the user
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': get_response_json(f'userinfo_v{version}'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(USERINFO_URLS[version]), Authorization='Bearer %s' % (first_access_token)
            )
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
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        @all_requests
        def catchall(url, req):

            return {
                'status_code': bfd_status_code,
                'content': get_response_json('resource_error_response'),
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(READ_UPDATE_DELETE_PATIENT_URLS[version], kwargs={'resource_id': DEFAULT_SAMPLE_FHIR_ID_V2}),
                Authorization='Bearer %s' % (first_access_token),
            )

            self.assertEqual(response.status_code, expected_code)

    @pytest.mark.integration
    def test_eob_request_when_thrown_when_invalid_parameters_included_v1_and_v2(self) -> None:
        for version in BAD_PARAMS_ACCEPTABLE_VERSIONS:
            url = SEARCH_EOB_URLS[version]
            self._test_request_when_invalid_parameters_included(url, version, HTTPStatus.OK, ENFORCE_PARAM_VALIDATION)

    @pytest.mark.integration
    def test_coverage_request_when_thrown_when_invalid_parameters_included_v1_and_v2(self) -> None:
        for version in BAD_PARAMS_ACCEPTABLE_VERSIONS:
            url = SEARCH_COVERAGE_URLS[version]
            self._test_request_when_invalid_parameters_included(url, version, HTTPStatus.OK, ENFORCE_PARAM_VALIDATION)

    @pytest.mark.integration
    def test_patient_request_when_thrown_when_invalid_parameters_included_v1_and_v2(self) -> None:
        for version in BAD_PARAMS_ACCEPTABLE_VERSIONS:
            url = SEARCH_PATIENT_URLS[version]
            self._test_request_when_invalid_parameters_included(url, version, HTTPStatus.OK, ENFORCE_PARAM_VALIDATION)

    @pytest.mark.integration
    def test_eob_request_when_thrown_when_invalid_parameters_and_prefer_strict_header_included_v3(self) -> None:
        url = SEARCH_EOB_URLS[Versions.V3]
        self._test_request_when_invalid_parameters_included(
            url, Versions.V3, HTTPStatus.BAD_REQUEST, ENFORCE_PARAM_VALIDATION
        )

    @pytest.mark.integration
    def test_coverage_request_when_thrown_when_invalid_parameters_and_prefer_strict_header_included_v3(self) -> None:
        url = SEARCH_COVERAGE_URLS[Versions.V3]
        self._test_request_when_invalid_parameters_included(
            url, Versions.V3, HTTPStatus.BAD_REQUEST, ENFORCE_PARAM_VALIDATION
        )

    @pytest.mark.integration
    def test_patient_request_when_invalid_parameters_and_prefer_strict_header_included_v3(self) -> None:
        url = SEARCH_PATIENT_URLS[Versions.V3]
        self._test_request_when_invalid_parameters_included(
            url, Versions.V3, HTTPStatus.BAD_REQUEST, ENFORCE_PARAM_VALIDATION
        )

    @pytest.mark.integration
    def test_eob_request_when_thrown_when_invalid_parameters_and_prefer_lenient_header_included_v3(self) -> None:
        url = SEARCH_EOB_URLS[Versions.V3]
        self._test_request_when_invalid_parameters_included(url, Versions.V3, HTTPStatus.OK, 'handling=lenient')

    @pytest.mark.integration
    def test_coverage_request_when_thrown_when_invalid_parameters_and_prefer_lenient_header_included_v3(self) -> None:
        url = SEARCH_COVERAGE_URLS[Versions.V3]
        self._test_request_when_invalid_parameters_included(url, Versions.V3, HTTPStatus.OK, 'handling=lenient')

    @pytest.mark.integration
    def test_patient_request_when_invalid_parameters_and_prefer_lenient_header_included_v3(self) -> None:
        url = SEARCH_PATIENT_URLS[Versions.V3]
        self._test_request_when_invalid_parameters_included(url, Versions.V3, HTTPStatus.OK, 'handling=lenient')

    @override_switch('v3_endpoints', active=True)
    def _test_request_when_invalid_parameters_included(
        self, url: str, version: int, expected_response_code: HTTPStatus, prefer_header: str
    ) -> None:
        """Ensure that a 400 is thrown for each type of resource call when invalid parameters are included for v3
        And that it is a 200 response when it is v1 or v2

        Args:
            url (str): The url that will be called in the test
            expected_bad_params (List[str]): The bad parameters that cause the 400 error to be thrown
        """
        # create the user
        first_access_token = self.create_token(
            'John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2, fhir_id_v3=DEFAULT_SAMPLE_FHIR_ID_V3
        )
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/Coverage.search patient/Patient.search patient/ExplanationOfBenefit.search'
        ac.save()

        response = self.client.get(
            reverse(url),
            {'hello': 'world'},
            Authorization='Bearer %s' % (first_access_token),
            HTTP_PREFER=prefer_header,
        )
        self.assertEqual(response.status_code, expected_response_code)
        if version == Versions.V3 and prefer_header == ENFORCE_PARAM_VALIDATION:
            self.assertEqual(response.json()['error'], "Invalid parameters: ['hello']")

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_call_eob_v3_ensure_source_is_added(self) -> None:
        """Ensure that if a v3 search EOB call is made, that the _source=NCH parameter
        is automatically added to the call, as there is no _tag or _source parameter already on the call
        """

        # create the user
        first_access_token = self.create_token(
            'John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2, fhir_id_v3=DEFAULT_SAMPLE_FHIR_ID_V3
        )
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/Coverage.search patient/Patient.search patient/ExplanationOfBenefit.search'
        ac.save()

        url = SEARCH_EOB_URLS[Versions.V3]
        response = self.client.get(
            reverse(url),
            {},
            Authorization='Bearer %s' % (first_access_token),
        )
        self.assertEqual(response.status_code, 200)
        assert DEFAULT_EOB_SOURCE in response.json()['link'][0]['url']

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_call_eob_v3_ensure_source_is_not_added(self) -> None:
        """Ensure that if a v3 search EOB call is made, and a _tag parameter is being passed,
        that the _source=NCH parameter is not added to the call
        """

        # create the user
        first_access_token = self.create_token(
            'John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2, fhir_id_v3=DEFAULT_SAMPLE_FHIR_ID_V3
        )
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/Coverage.search patient/Patient.search patient/ExplanationOfBenefit.search'
        ac.save()

        url = reverse(SEARCH_EOB_URLS[Versions.V3])
        url += '/?_tag=https://bluebutton.cms.gov/fhir/CodeSystem/System-Type|NationalClaimsHistory'
        response = self.client.get(
            url,
            {},
            Authorization='Bearer %s' % (first_access_token),
        )
        self.assertEqual(response.status_code, 200)
        assert DEFAULT_EOB_SOURCE not in response.json()['link'][0]['url']

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_call_eob_v3_include_samhsa_is_false(self) -> None:
        """Ensure that if a v3 search EOB call is made, and if the oauth2_provider_accesstoken_extension record
        associated with the request has include_samhsa of false, that the _security:not=42CFRPart2 is added to the
        request
        """
        # create the user
        first_access_token = self.create_token(
            'John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2, fhir_id_v3=DEFAULT_SAMPLE_FHIR_ID_V3
        )
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/ExplanationOfBenefit.rs'
        ac.save()

        token_extension = AccessTokenExtension.objects.get(access_token=ac)
        token_extension.include_samhsa = False
        token_extension.save()

        url = SEARCH_EOB_URLS[Versions.V3]
        response = self.client.get(
            reverse(url),
            {},
            HTTP_AUTHORIZATION='Bearer %s' % first_access_token,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        assert EXCLUDE_SAMHSA_PARAMETER_VALUE in response.json()['link'][0]['url']

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_call_eob_v3_include_samhsa_is_true(self) -> None:
        """Ensure that if a v3 search EOB call is made, and if the oauth2_provider_accesstoken_extension record
        associated with the request has include_samhsa of true, that the _security:not=42CFRPart2 is NOT added to the
        request
        """
        # create the user
        first_access_token = self.create_token(
            'John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2, fhir_id_v3=DEFAULT_SAMPLE_FHIR_ID_V3
        )
        ac = AccessToken.objects.get(token=first_access_token)
        ac.scope = 'patient/ExplanationOfBenefit.rs'
        ac.save()

        url = reverse(SEARCH_EOB_URLS[Versions.V3])
        response = self.client.get(
            url,
            {},
            HTTP_AUTHORIZATION='Bearer %s' % first_access_token,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        assert EXCLUDE_SAMHSA_PARAMETER_VALUE not in response.json()['link'][0]['url']

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_v3_eob_call_succeeds(self):
        """
        Ensure that a v3 EOB call succeeds despite the presence of SamhsaPermission.
        """
        ac = self.create_token(
            'John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2, fhir_id_v3=DEFAULT_SAMPLE_FHIR_ID_V3
        )
        response = self.client.get(reverse(SEARCH_EOB_URLS[Versions.V3]), Authorization=f'Bearer {ac}')
        self.assertEqual(response.status_code, 200)

    @pytest.mark.integration
    def test_v12_no_extension_succeeds(self):
        """
        Ensure that a v1/2 call for a token with no AccessTokenExtension succeeds.
        """
        ac = self.create_token(
            'John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2, fhir_id_v3=DEFAULT_SAMPLE_FHIR_ID_V3
        )
        AccessToken.objects.get(token=ac).accesstokenextension.delete()
        self.assertFalse(AccessTokenExtension.objects.all().exists())

        for version in [Versions.V1, Versions.V2]:
            response = self.client.get(reverse(SEARCH_EOB_URLS[version]), Authorization=f'Bearer {ac}')
            self.assertEqual(response.status_code, 200)

    @pytest.mark.integration
    def test_v12_include_samhsa_false_fails(self):
        """
        Ensure that a v1/2 call for a token with AccessTokenExtension.include_samhsa==False fails
        """
        ac = self.create_token(
            'John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2, fhir_id_v3=DEFAULT_SAMPLE_FHIR_ID_V3
        )
        extension = AccessToken.objects.get(token=ac).accesstokenextension
        extension.include_samhsa = False
        extension.save()

        for version in [Versions.V1, Versions.V2]:
            response = self.client.get(reverse(SEARCH_EOB_URLS[version]), Authorization=f'Bearer {ac}')
            self.assertEqual(response.status_code, 403)
            self.assertDictEqual(response.json(), {'detail': 'You do not have permission to perform this action.'})

    @pytest.mark.integration
    def test_v12_include_samhsa_true_succeeds(self):
        """
        Ensure that a v1/2 call for a token with AccessTokenExtension.include_samhsa==True succeeds
        """
        ac = self.create_token(
            'John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2, fhir_id_v3=DEFAULT_SAMPLE_FHIR_ID_V3
        )
        extension = AccessToken.objects.get(token=ac).accesstokenextension
        extension.include_samhsa = True
        extension.save()

        for version in [Versions.V1, Versions.V2]:
            response = self.client.get(reverse(SEARCH_EOB_URLS[version]), Authorization=f'Bearer {ac}')
            self.assertEqual(response.status_code, 200)

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_matching_patient_scope_returns_200(self):
        """
        Returns a 200 since the patient resource is for a patient and they are trying to make a patient call.
        """
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        response = self.client.get(
            reverse(SEARCH_PATIENT_URLS[Versions.V3]), Authorization=f'Bearer {first_access_token}'
        )
        self.assertEqual(response.status_code, 200)

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_matching_coverage_scope_returns_200(self):
        """
        Returns a 200 since the coverage resource is for coverage and they are trying to make a coverage call.
        """
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        response = self.client.get(
            reverse(SEARCH_COVERAGE_URLS[Versions.V3]), Authorization=f'Bearer {first_access_token}'
        )
        self.assertEqual(response.status_code, 200)

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_matching_eob_scope_returns_200(self):
        """
        Returns a 200 since the eob resource is for eob and they are trying to make a eob call.
        """
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        response = self.client.get(reverse(SEARCH_EOB_URLS[Versions.V3]), Authorization=f'Bearer {first_access_token}')
        self.assertEqual(response.status_code, 200)

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_no_matching_patient_scope_returns_403(self):
        """
        Returns a 403 since the patient resource is removed from the database and they are trying to make a patient call.
        """
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        # Remove the patient scope for that app and try to make a call
        application = Application.objects.get(name='John_Smith_test')
        patient_scope = ProtectedCapability.objects.get(slug=PATIENT_SCOPE)
        application.scope.remove(patient_scope)

        response = self.client.get(
            reverse(SEARCH_PATIENT_URLS[Versions.V3]), Authorization=f'Bearer {first_access_token}'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()['detail'],
            APPLICATION_DOES_NOT_HAVE_VALID_SCOPES.format('John_Smith_test', 'search', 'Patient'),
        )

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_no_matching_patient_search_scope_returns_403(self):
        """
        Returns a 403 since the patient only has a patient read scope and they are trying to make a patient search call.
        """
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        # Remove the patient search scope for that app
        application = Application.objects.get(name='John_Smith_test')
        patient_protected_resource = ProtectedCapability.objects.get(slug=PATIENT_SCOPE)
        application.scope.remove(patient_protected_resource)

        # Add just a read scope
        patient_read_capability = ProtectedCapability.objects.get(slug='patient/Patient.r')
        application.scope.add(patient_read_capability)

        # Try to make a search fhir request
        response = self.client.get(
            reverse(SEARCH_PATIENT_URLS[Versions.V3]), Authorization=f'Bearer {first_access_token}'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()['detail'],
            APPLICATION_DOES_NOT_HAVE_VALID_SCOPES.format('John_Smith_test', 'search', 'Patient'),
        )

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_no_matching_coverage_scope_returns_403(self):
        """
        Returns a 403 since the coverage resource is removed from the database and they are trying to make a coverage call.
        """
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        # Remove the coverage scope for that app and try to make a call
        application = Application.objects.get(name='John_Smith_test')
        coverage_protected_resource = ProtectedCapability.objects.get(slug=COVERAGE_SCOPE)
        application.scope.remove(coverage_protected_resource)

        response = self.client.get(
            reverse(SEARCH_COVERAGE_URLS[Versions.V3]), Authorization=f'Bearer {first_access_token}'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()['detail'],
            APPLICATION_DOES_NOT_HAVE_VALID_SCOPES.format('John_Smith_test', 'search', 'Coverage'),
        )

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_no_matching_coverage_search_scope_returns_403(self):
        """
        Returns a 403 since the patient only has a coverage read scope and they are trying to make a coverage search call.
        """
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        # Remove the coverage search scope for that app
        application = Application.objects.get(name='John_Smith_test')
        coverage_protected_resource = ProtectedCapability.objects.get(slug=COVERAGE_SCOPE)
        application.scope.remove(coverage_protected_resource)

        # Add just a read scope
        coverage_read_capability = ProtectedCapability.objects.get(slug='patient/Coverage.r')
        application.scope.add(coverage_read_capability)

        # Try to make a search fhir request
        response = self.client.get(
            reverse(SEARCH_COVERAGE_URLS[Versions.V3]), Authorization=f'Bearer {first_access_token}'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()['detail'],
            APPLICATION_DOES_NOT_HAVE_VALID_SCOPES.format('John_Smith_test', 'search', 'Coverage'),
        )

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_no_matching_eob_scope_returns_403(self):
        """
        Returns a 403 since the eob resource is removed from the database and they are trying to make an eob call.
        """
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        # Remove the eob scope for that app and try to make a call
        application = Application.objects.get(name='John_Smith_test')
        eob_protected_resource = ProtectedCapability.objects.get(slug=EOB_SCOPE)
        application.scope.remove(eob_protected_resource)

        response = self.client.get(reverse(SEARCH_EOB_URLS[Versions.V3]), Authorization=f'Bearer {first_access_token}')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()['detail'],
            APPLICATION_DOES_NOT_HAVE_VALID_SCOPES.format('John_Smith_test', 'search', 'ExplanationOfBenefit'),
        )

    @pytest.mark.integration
    @override_switch('v3_endpoints', active=True)
    def test_no_matching_eob_search_scope_returns_403(self):
        """
        Returns a 403 since the patient only has an eob read scope and they are trying to make an eob search call.
        """
        first_access_token = self.create_token('John', 'Smith', fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        # Remove the patient search scope for that app
        application = Application.objects.get(name='John_Smith_test')
        eob_protected_resource = ProtectedCapability.objects.get(slug=EOB_SCOPE)
        application.scope.remove(eob_protected_resource)

        # Add just a read scope
        eob_read_capability = ProtectedCapability.objects.get(slug='patient/ExplanationOfBenefit.r')
        application.scope.add(eob_read_capability)

        # Try to make a search fhir request
        response = self.client.get(reverse(SEARCH_EOB_URLS[Versions.V3]), Authorization=f'Bearer {first_access_token}')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()['detail'],
            APPLICATION_DOES_NOT_HAVE_VALID_SCOPES.format('John_Smith_test', 'search', 'ExplanationOfBenefit'),
        )
