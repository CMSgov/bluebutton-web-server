import json

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from oauth2_provider.models import AccessToken
from rest_framework.test import APIClient
from waffle.testutils import override_switch

from apps.test import BaseApiTest
from apps.testclient.utils import extract_last_page_index
from .common_utils import validate_json_schema
from .endpoint_schemas import (COVERAGE_READ_SCHEMA_V2,
                               EOB_READ_INPT_SCHEMA,
                               FHIR_META_SCHEMA,
                               USERINFO_SCHEMA,
                               PATIENT_READ_SCHEMA,
                               PATIENT_SEARCH_SCHEMA,
                               COVERAGE_READ_SCHEMA,
                               COVERAGE_SEARCH_SCHEMA,
                               EOB_READ_SCHEMA,
                               EOB_SEARCH_SCHEMA)


C4BB_PROFILE_URLS = {
    "COVERAGE": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-Coverage",
    "PATIENT": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-Patient",
    "INPATIENT": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Inpatient-Institutional",
    "OUTPATIENT": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Outpatient-Institutional",
    "PHARMACY": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Pharmacy",
    "NONCLINICIAN": "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Professional-NonClinician",
}

SAMPLE_A_888_MBI_HASH = '37c37d08d239f7f1da60e949674c8e4b5bb2106077cb0671d3dfcbf510ec3248'
SAMPLE_A_888_HICN_HASH = '3637b48c050b8d7a3aa29cd012a535c0ab0e52fe18ddcf1863266b217adc242f'

FHIR_RES_TYPE_EOB = "ExplanationOfBenefit"
FHIR_RES_TYPE_PATIENT = "Patient"
FHIR_RES_TYPE_COVERAGE = "Coverage"


def dump_content(json_str, file_name):
    text_file = open(file_name, "w")
    text_file.write(json_str)
    text_file.close()


class IntegrationTestFhirApiResources(StaticLiveServerTestCase):
    '''
    This sets up a live server in the background to test with.
    For more details, see https://docs.djangoproject.com/en/3.1/topics/testing/tools/#liveservertestcase
    This uses APIClient to test the BB2 FHIR API endpoints with the default (Fred) access token.
    '''
    fixtures = ['scopes.json']

    def setUp(self):
        super().setUp()

    def _get_fhir_url(self, resource_name, params, v2=False):
        endpoint_url = "{}/{}/fhir/{}".format(self.live_server_url, 'v2' if v2 else 'v1', resource_name)
        if params is not None:
            endpoint_url = "{}/{}".format(endpoint_url, params)
        return endpoint_url

    def _setup_apiclient(self, client, fn=None, ln=None, fhir_id=None, hicn_hash=None, mbi_hash=None):
        # Setup token in APIClient
        '''
        TODO: Perform auth flow here --- when selenium is included later.
              For now, creating user thru access token using BaseApiTest for now.
        '''
        # Setup instance of BaseApiTest
        base_api_test = BaseApiTest()

        # Setup client for BaseApiTest client
        base_api_test.client = client

        # Setup read/write capability for create_token()
        base_api_test.read_capability = base_api_test._create_capability('Read', [])
        base_api_test.write_capability = base_api_test._create_capability('Write', [])

        # create user, app, and access token
        first_name = fn if fn is not None else "John"
        last_name = ln if ln is not None else "Doe"
        access_token = base_api_test.create_token(first_name, last_name, fhir_id, hicn_hash, mbi_hash)

        # Test scope in access_token
        at = AccessToken.objects.get(token=access_token)

        # Setup Bearer token:
        client.credentials(HTTP_AUTHORIZATION="Bearer " + at.token)

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

    def _assertAddressOK(self, resource):
        addr_list = resource.get('address')
        self.assertIsNotNone(addr_list)
        for a in addr_list:
            self.assertIsNotNone(a.get('state'))
            self.assertIsNotNone(a.get('postalCode'))
            self.assertIsNone(a.get('line'))
            self.assertIsNone(a.get('city'))

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

    def _extract_urls(self, relations):
        nav_info = {}
        for r in relations:
            nav_info[r.get('relation')] = r.get('url', None)
        return nav_info

    def _stats_resource_by_type(self, bundle_json, cur_stats_dict, schema=None):

        for e in bundle_json['entry']:

            rs = e['resource']
            rs_id = rs['id']

            if schema is not None:
                eob_profile = rs['meta']['profile'][0]
                self.assertIsNotNone(eob_profile)
                self.assertTrue(validate_json_schema(schema, rs))

            is_matched = False

            for t in cur_stats_dict:
                if rs_id.startswith(t):
                    is_matched = True
                    cur_stats_dict[t] = int(cur_stats_dict[t]) + 1
                    break

            self.assertTrue(is_matched, 'Unexpected resource id prefix encountered, id={}'.format(rs_id))

    def test_health_endpoint(self):
        client = APIClient()
        # no authenticate needed
        response = client.get(self.live_server_url + "/health")
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        msg = None
        try:
            msg = content['message']
        except KeyError:
            pass
        self.assertEqual(msg, "all's well")

    # Commenting the following resulting some failures in the Cloudbees CI
    # in contacting the test.accounts.cms.gov servers

    # @override_switch('require-scopes', active=True)
    # def test_health_external_endpoint(self):
    #     self._call_health_external_endpoint(False)

    # @override_switch('require-scopes', active=True)
    # def test_health_external_endpoint_v2(self):
    #     self._call_health_external_endpoint(True)

    # def _call_health_external_endpoint(self, v2=False):
    #     use_mslsx = os.environ.get('USE_MSLSX', None)
    #     if use_mslsx is not None and not use_mslsx == 'true':
    #         # do not ping health end point if using MSLSX
    #         client = APIClient()
    #         # no authenticate needed
    #         response = client.get(self.live_server_url + "/health/external_v2" if v2 else "/health/external")
    #         self.assertEqual(response.status_code, 200)
    #         content = json.loads(response.content)
    #         msg = None
    #         try:
    #             msg = content['message']
    #         except KeyError:
    #             pass
    #         self.assertEqual(msg, "all's well")

    # @override_switch('require-scopes', active=True)
    # def test_health_bfd_endpoint(self):
    #     self._call_health_bfd_endpoint(False)

    # @override_switch('require-scopes', active=True)
    # def test_health_bfd_endpoint_v2(self):
    #     self._call_health_bfd_endpoint(True)

    # def _call_health_bfd_endpoint(self, v2=False):
    #     client = APIClient()
    #     # no authenticate needed
    #     response = client.get(self.live_server_url + "/health/bfd_v2" if v2 else "/health/bfd")
    #     self.assertEqual(response.status_code, 200)
    #     content = json.loads(response.content)
    #     msg = None
    #     try:
    #         msg = content['message']
    #     except KeyError:
    #         pass
    #     self.assertEqual(msg, "all's well")

    # @override_switch('require-scopes', active=True)
    # def test_health_db_endpoint(self):
    #     client = APIClient()
    #     # no authenticate needed
    #     response = client.get(self.live_server_url + "/health/db")
    #     self.assertEqual(response.status_code, 200)
    #     content = json.loads(response.content)
    #     msg = None
    #     try:
    #         msg = content['message']
    #     except KeyError:
    #         pass
    #     self.assertEqual(msg, "all's well")

    # @override_switch('require-scopes', active=True)
    # def test_health_sls_endpoint(self):
    #     use_mslsx = os.environ.get('USE_MSLSX', None)
    #     if use_mslsx is not None and not use_mslsx == 'true':
    #         # do not ping health end point if using MSLSX
    #         client = APIClient()
    #         # no authenticate needed
    #         response = client.get(self.live_server_url + "/health/sls")
    #         self.assertEqual(response.status_code, 200)
    #         content = json.loads(response.content)
    #         msg = None
    #         try:
    #             msg = content['message']
    #         except KeyError:
    #             pass
    #         self.assertEqual(msg, "all's well")

    @override_switch('require-scopes', active=True)
    def test_userinfo_endpoint(self):
        self._call_userinfo_endpoint(False)

    @override_switch('require-scopes', active=True)
    def test_userinfo_endpoint_v2(self):
        self._call_userinfo_endpoint(True)

    def _call_userinfo_endpoint(self, v2=False):
        base_path = "/{}/connect/userinfo".format('v2' if v2 else 'v1')
        client = APIClient()

        # 1. Test unauthenticated request
        url = self.live_server_url + base_path
        response = client.get(url)
        self.assertEqual(response.status_code, 401)

        # Authenticate
        self._setup_apiclient(client)

        # 2. Test authenticated request
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        #     Validate JSON Schema
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "userinfo_{}.json".format('v2' if v2 else 'v1'))
        self.assertEqual(validate_json_schema(USERINFO_SCHEMA, content), True)

    @override_switch('require-scopes', active=True)
    def test_fhir_meta_endpoint(self):
        self._call_fhir_meta_endpoint(False)

    @override_switch('require-scopes', active=True)
    def test_fhir_meta_endpoint_v2(self):
        self._call_fhir_meta_endpoint(True)

    def _call_fhir_meta_endpoint(self, v2=False):
        client = APIClient()
        # 1. Test unauthenticated request, no auth needed for capabilities
        response = client.get(self._get_fhir_url("metadata", None, v2))
        self.assertEqual(response.status_code, 200)

        # Authenticate
        self._setup_apiclient(client)

        # 2. Test authenticated request
        response = client.get(self._get_fhir_url("metadata", None, v2))
        self.assertEqual(response.status_code, 200)
        # Validate JSON Schema
        content = json.loads(response.content)
        fhir_ver = None
        try:
            fhir_ver = content['fhirVersion']
        except KeyError:
            pass
        self.assertIsNotNone(fhir_ver)
        # match any FHIR ver 4.0.*
        versionOK = fhir_ver and fhir_ver.startswith('4.0.' if v2 else '3.0.2')
        self.assertTrue(versionOK)
        self.assertEqual(validate_json_schema(FHIR_META_SCHEMA, content), True)

    @override_switch('require-scopes', active=True)
    def test_patient_endpoint(self):
        '''
        test patient read and search v1
        '''
        self._call_patient_endpoint(False)

    @override_switch('require-scopes', active=True)
    def test_patient_endpoint_v2(self):
        '''
        test patient read and search v2
        '''
        self._call_patient_endpoint(True)

    def _call_patient_endpoint(self, v2=False):
        client = APIClient()
        # 1. Test unauthenticated request
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_PATIENT, None, v2))
        self.assertEqual(response.status_code, 401)

        # Authenticate
        self._setup_apiclient(client)

        # 2. Test SEARCH VIEW endpoint
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_PATIENT, None, v2))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "patient_search_{}.json".format('v2' if v2 else 'v1'))
        # Validate JSON Schema
        self.assertEqual(validate_json_schema(PATIENT_SEARCH_SCHEMA, content), True)

        for r in content['entry']:
            resource = r['resource']
            self._assertHasC4BBProfile(resource, C4BB_PROFILE_URLS['PATIENT'], v2)
            # Assert address does not contain address details
            self._assertAddressOK(resource)

        # 3. Test READ VIEW endpoint
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_PATIENT, settings.DEFAULT_SAMPLE_FHIR_ID, v2))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "patient_read_{}.json".format('v2' if v2 else 'v1'))
        # Validate JSON Schema
        # now v2 returns patient without identifier - think it's a bug, by-pass v2 assert to BB2 IT temporarily
        # until BFD resolve this.
        if not v2:
            self.assertEqual(validate_json_schema(PATIENT_READ_SCHEMA, content), True)

        self._assertHasC4BBProfile(content, C4BB_PROFILE_URLS['PATIENT'], v2)
        # Assert there is no address lines and city in patient.address (BFD-379)
        self._assertAddressOK(content)

        # 5. Test unauthorized READ request
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_PATIENT, '99999999999999', v2))
        self.assertEqual(response.status_code, 404)

    @override_switch('require-scopes', active=True)
    def test_coverage_endpoint(self):
        '''
        Search and read Coverage v1
        '''
        self._call_coverage_endpoint(False)

    @override_switch('require-scopes', active=True)
    def test_coverage_endpoint_v2(self):
        '''
        Search and read Coverage v2
        '''
        self._call_coverage_endpoint(True)

    def _call_coverage_endpoint(self, v2=False):
        client = APIClient()
        # 1. Test unauthenticated request
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_COVERAGE, None, v2))
        self.assertEqual(response.status_code, 401)

        # Authenticate
        self._setup_apiclient(client)

        # 2. Test SEARCH VIEW endpoint
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_COVERAGE, None, v2))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "coverage_search_{}.json".format('v2' if v2 else 'v1'))
        # Validate JSON Schema
        self.assertEqual(validate_json_schema(COVERAGE_SEARCH_SCHEMA, content), True)

        # 3. Test READ VIEW endpoint
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_COVERAGE, "part-a-" + settings.DEFAULT_SAMPLE_FHIR_ID, v2))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "coverage_read_{}.json".format('v2' if v2 else 'v1'))
        # Validate JSON Schema
        self._assertHasC4BBProfile(content, C4BB_PROFILE_URLS['COVERAGE'], v2)
        self.assertEqual(validate_json_schema(COVERAGE_READ_SCHEMA_V2 if v2 else COVERAGE_READ_SCHEMA, content), True)

        # 4. Test unauthorized READ request
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_COVERAGE, "part-a-99999999999999", v2))
        self.assertEqual(response.status_code, 404)

    @override_switch('require-scopes', active=True)
    def test_coverage_search_endpoint(self):
        '''
        Search Coverage v1, navigate pages and collect stats
        '''
        self._call_coverage_search_endpoint(False)

    @override_switch('require-scopes', active=True)
    def test_coverage_search_endpoint_v2(self):
        '''
        Search Coverage v2, navigate pages and collect stats
        '''
        self._call_coverage_search_endpoint(True)

    def _call_coverage_search_endpoint(self, v2=False):
        client = APIClient()

        # Authenticate
        self._setup_apiclient(client)

        # Coverage search endpoint
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_COVERAGE, None, v2))
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)
        # dump_content(json.dumps(content), "coverage_search_nav_p{}_{}.json".format(0, 'v2' if v2 else 'v1'))

        # Validate JSON Schema: bundle with entries and link section with page navigation: first, next, previous, last, self
        self.assertEqual(validate_json_schema(COVERAGE_SEARCH_SCHEMA, content), True)

        total_page = self._get_total_page(content)
        assert total_page >= 0
        # count = 10
        # page_total = (total + count) // count

        expected_resource_stats = {'part-a': 1, 'part-b': 1, 'part-c': 1, 'part-d': 1}
        resource_stats = {'part-a': 0, 'part-b': 0, 'part-c': 0, 'part-d': 0}
        self._stats_resource_by_type(content, resource_stats)

        for i in range(total_page):
            lnk = content.get('link', None)
            self.assertIsNotNone(lnk,
                                 ("Field 'link' expected, "
                                  "containing page navigation urls e.g. 'first', 'next', 'self', 'previous', 'last' "))
            nav_info = self._extract_urls(lnk)
            if nav_info.get('next', None) is not None:
                response = client.get(nav_info['next'])
                self.assertEqual(response.status_code, 200)
                content = json.loads(response.content)
                self._stats_resource_by_type(content, resource_stats)
                # dump_content(json.dumps(content), "coverage_search_nav_p{}_{}.json".format(i+1, 'v2' if v2 else 'v1'))
            else:
                # last page does not have 'next'
                break

        # assert resource stats of sample A:
        self.assertEqual(resource_stats['part-a'], expected_resource_stats['part-a'])
        self.assertEqual(resource_stats['part-b'], expected_resource_stats['part-b'])
        self.assertEqual(resource_stats['part-c'], expected_resource_stats['part-c'])
        self.assertEqual(resource_stats['part-d'], expected_resource_stats['part-d'])

    @override_switch('require-scopes', active=True)
    def test_eob_search_endpoint(self):
        '''
        Search EOB v1, navigate pages and collect stats of different types of claims
        e.g. pde, carrier, outpatient, inpatient, etc.

        Also validate sample A stats - consistent with IG documentation:

        total claim: 70

        carrier: 50
        pde: 10
        inpatient: 4
        outpatient: 6

        '''
        self._call_eob_search_endpoint(False)

    @override_switch('require-scopes', active=True)
    def test_eob_search_endpoint_v2(self):
        '''
        Search EOB v2, navigate pages and collect stats of different types of claims
        e.g. pde, carrier, outpatient, inpatient, etc.
        '''
        self._call_eob_search_endpoint(True)

    def _call_eob_search_endpoint(self, v2=False):
        client = APIClient()

        # Authenticate
        self._setup_apiclient(client)

        # EOB search endpoint
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, None, v2))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "eob_search_nav_p{}_{}.json".format(0, 'v2' if v2 else 'v1'))

        # Validate JSON Schema: bundle with entries and link section with page navigation: first, next, previous, last, self
        self.assertEqual(validate_json_schema(EOB_SEARCH_SCHEMA, content), True)

        total_page = self._get_total_page(content)
        # total = content['total']
        # count = 10
        # page_total = (total + count) // count
        assert total_page >= 0

        expected_resource_stats = {'pde': 5, 'carrier': 25, 'inpatient': 2, 'outpatient': 6}
        resource_stats = {'pde': 0, 'carrier': 0, 'inpatient': 0, 'outpatient': 0}
        self._stats_resource_by_type(content, resource_stats)

        for i in range(total_page):
            lnk = content.get('link', None)
            self.assertIsNotNone(lnk, ("Field 'link' expected, "
                                 "containing page navigation urls e.g. 'first', 'next', 'self', 'previous', 'last' "))
            nav_info = self._extract_urls(lnk)
            if nav_info.get('next', None) is not None:
                response = client.get(nav_info['next'])
                self.assertEqual(response.status_code, 200)
                content = json.loads(response.content)
                self._stats_resource_by_type(content, resource_stats)
                # dump_content(json.dumps(content), "eob_search_nav_p{}_{}.json".format(i+1, 'v2' if v2 else 'v1'))
            else:
                # last page does not have 'next'
                break

        # assert eob claims resource stats of sample A:
        self.assertEqual(resource_stats['pde'], expected_resource_stats['pde'])
        self.assertEqual(resource_stats['carrier'], expected_resource_stats['carrier'])
        self.assertEqual(resource_stats['inpatient'], expected_resource_stats['inpatient'])
        self.assertEqual(resource_stats['outpatient'], expected_resource_stats['outpatient'])

    @override_switch('require-scopes', active=True)
    def test_eob_profiles_endpoint(self):
        client = APIClient()

        # Authenticate
        self._setup_apiclient(client,
                              'sample_a_88888888888888',
                              'sample_a_88888888888888',
                              '-88888888888888',
                              SAMPLE_A_888_HICN_HASH,
                              SAMPLE_A_888_MBI_HASH)

        # EOB search endpoint
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, None, True))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "eob_search_profiles_888888888888.json")

        # Validate JSON Schema: bundle with entries and link section with page navigation: first, next, previous, last, self
        # comment out since the C4BB EOB resources do not validate with FHIR R4 json schema
        self.assertEqual(validate_json_schema(EOB_SEARCH_SCHEMA, content), True)

        total_page = self._get_total_page(content)
        # total = content['total']
        # count = 10
        # page_total = (total + count) // count
        assert total_page >= 0

        expected_resource_stats = {
            'pde': 1, 'carrier': 1, 'inpatient': 1, 'outpatient': 1, 'dme': 1, 'snf': 1, 'hha': 1, 'hospice': 1, }
        resource_stats = {
            'pde': 0, 'carrier': 0, 'inpatient': 0, 'outpatient': 0, 'dme': 0, 'snf': 0, 'hha': 0, 'hospice': 0, }
        self._stats_resource_by_type(content, resource_stats)

        for i in range(total_page):
            lnk = content.get('link', None)
            self.assertIsNotNone(lnk,
                                 ("Field 'link' expected, "
                                  "containing page navigation urls e.g. 'first', 'next', 'self', 'previous', 'last' "))
            nav_info = self._extract_urls(lnk)
            if nav_info.get('next', None) is not None:
                response = client.get(nav_info['next'])
                self.assertEqual(response.status_code, 200)
                content = json.loads(response.content)
                self._stats_resource_by_type(content, resource_stats)
                # dump_content(json.dumps(content), "eob_search_profiles_p{}.json".format(i + 1))
            else:
                # last page does not have 'next'
                break

        # assert eob claims resource stats of sample A:
        self.assertEqual(resource_stats['pde'], expected_resource_stats['pde'])
        self.assertEqual(resource_stats['carrier'], expected_resource_stats['carrier'])
        self.assertEqual(resource_stats['inpatient'], expected_resource_stats['inpatient'])
        self.assertEqual(resource_stats['outpatient'], expected_resource_stats['outpatient'])
        self.assertEqual(resource_stats['dme'], expected_resource_stats['dme'])
        self.assertEqual(resource_stats['snf'], expected_resource_stats['snf'])
        self.assertEqual(resource_stats['hha'], expected_resource_stats['hha'])
        self.assertEqual(resource_stats['hospice'], expected_resource_stats['hospice'])

    @override_switch('require-scopes', active=True)
    def test_eob_endpoint(self):
        '''
        Search and read EOB v1
        '''
        self._call_eob_endpoint(False)

    @override_switch('require-scopes', active=True)
    def test_eob_endpoint_v2(self):
        '''
        Search and read EOB v2
        '''
        self._call_eob_endpoint(True)

    def _call_eob_endpoint(self, v2=False):
        client = APIClient()
        # 1. Test unauthenticated request
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, None, v2))
        self.assertEqual(response.status_code, 401)

        # Authenticate
        self._setup_apiclient(client)

        # 2. Test SEARCH VIEW endpoint, default to current bene's PDE
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, None, v2))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(validate_json_schema(EOB_SEARCH_SCHEMA, content), True)
        # dump_content(json.dumps(content), "eob_search_{}.json".format('v2' if v2 else 'v1'))
        # Validate JSON Schema
        for r in content['entry']:
            self._assertHasC4BBProfile(r['resource'],
                                       C4BB_PROFILE_URLS['NONCLINICIAN'],
                                       v2)

        # 3. Test READ VIEW endpoint v1 (carrier) and v2
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, "carrier--22639159481", v2))
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "eob_read_carrier_{}.json".format('v2' if v2 else 'v1'))
        self.assertEqual(response.status_code, 200)
        if not v2:
            # Validate JSON Schema
            self.assertEqual(validate_json_schema(EOB_READ_SCHEMA, content), True)
        self._assertHasC4BBProfile(content, C4BB_PROFILE_URLS['NONCLINICIAN'], v2)

        # 4. Test SEARCH VIEW endpoint v1 and v2 (BB2-418 EOB V2 PDE profile)
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, "?patient=-20140000008325", v2))
        self.assertEqual(response.status_code, 200)
        # Validate JSON Schema
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "eob_search_pt_{}.json".format('v2' if v2 else 'v1'))
        self.assertEqual(validate_json_schema(EOB_SEARCH_SCHEMA, content), True)
        for r in content['entry']:
            self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['NONCLINICIAN'], v2)

        # 5. Test unauthorized READ request
        # same asserts for v1 and v2
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, "carrier--23017401521", v2))
        self.assertEqual(response.status_code, 404)

    @override_switch('require-scopes', active=True)
    def test_eob_endpoint_pde(self):
        '''
        EOB pde (pharmacy) profile v1
        '''
        self._call_eob_endpoint_pde(False)

    @override_switch('require-scopes', active=True)
    def test_eob_endpoint_pde_v2(self):
        '''
        EOB pde (pharmacy) profile v2
        '''
        self._call_eob_endpoint_pde(True)

    def _call_eob_endpoint_pde(self, v2=False):
        client = APIClient()
        # Authenticate
        self._setup_apiclient(client)
        # read eob pde profile v1 and v2
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, "pde--4894712975", v2))
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "eob_read_pde_{}.json".format('v2' if v2 else 'v1'))
        self.assertEqual(response.status_code, 200)
        if not v2:
            # Validate JSON Schema for v1
            self.assertEqual(validate_json_schema(EOB_READ_INPT_SCHEMA, content), True)
        self._assertHasC4BBProfile(content, C4BB_PROFILE_URLS['PHARMACY'], v2)

    @override_switch('require-scopes', active=True)
    def test_eob_endpoint_inpatient(self):
        self._call_eob_endpoint_inpatient(False)

    @override_switch('require-scopes', active=True)
    def test_eob_endpoint_inpatient_v2(self):
        self._call_eob_endpoint_inpatient(True)

    def _call_eob_endpoint_inpatient(self, v2=False):
        client = APIClient()
        # Authenticate
        self._setup_apiclient(client)
        # Test READ VIEW endpoint v1 and v2: inpatient
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, "inpatient--4436342082", v2))
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "eob_read_in_pt_{}.json".format('v2' if v2 else 'v1'))
        self.assertEqual(response.status_code, 200)
        if not v2:
            # Validate JSON Schema v1
            self.assertEqual(validate_json_schema(EOB_READ_INPT_SCHEMA, content), True)
        self._assertHasC4BBProfile(content, C4BB_PROFILE_URLS['INPATIENT'], v2)

    def _get_total_page(self, content):
        total_page = -1
        links = content.get('link', None)
        if links:
            nav_info = self._extract_urls(links)
            total_page = extract_last_page_index(nav_info['last'])
        return total_page

    @override_switch('require-scopes', active=True)
    def test_eob_endpoint_outpatient(self):
        self._call_eob_endpoint_outpatient(False)

    @override_switch('require-scopes', active=True)
    def test_eob_endpoint_outpatient_v2(self):
        self._call_eob_endpoint_outpatient(True)

    def _call_eob_endpoint_outpatient(self, v2=False):
        client = APIClient()
        # Authenticate
        self._setup_apiclient(client)
        # Test READ VIEW endpoint v1 and v2: outpatient
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, "outpatient--4412920419", v2))
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "eob_read_out_pt_{}.json".format('v2' if v2 else 'v1'))
        self.assertEqual(response.status_code, 200)
        if not v2:
            # Validate JSON Schema v1
            self.assertEqual(validate_json_schema(EOB_READ_INPT_SCHEMA, content), True)
        else:
            self.assertEqual(response.status_code, 200)
        self._assertHasC4BBProfile(content, C4BB_PROFILE_URLS['OUTPATIENT'], v2)

    @override_switch('require-scopes', active=True)
    def test_err_response_caused_by_illegalarguments(self):
        self._err_response_caused_by_illegalarguments(False)

    @override_switch('require-scopes', active=True)
    def test_err_response_caused_by_illegalarguments_v2(self):
        self._err_response_caused_by_illegalarguments(True)

    def _err_response_caused_by_illegalarguments(self, v2=False):
        client = APIClient()
        # Authenticate
        self._setup_apiclient(client)
        response = client.get(self._get_fhir_url(FHIR_RES_TYPE_COVERAGE, "part-d___--20140000008325", v2))
        # This now returns 400 after BB2-2063 work.
        # for both v1 and v2
        self.assertEqual(response.status_code, 400)
