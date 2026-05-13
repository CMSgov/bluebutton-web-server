from http import HTTPStatus
from urllib.parse import urlparse

from django.core.management import call_command
from django.test import tag
from rest_framework.test import APIClient
from waffle.testutils import override_switch

from apps.constants import (
    C4BB_PROFILE_URLS,
    DEFAULT_SAMPLE_FHIR_ID_V2,
    DEFAULT_SAMPLE_FHIR_ID_V3,
    FHIR_RES_TYPE_EOB,
    FHIR_RES_TYPE_PATIENT,
    OPERATION_OUTCOME,
)
from apps.core.models import Flag
from apps.integration_tests.common_utils import validate_json_schema
from apps.integration_tests.constants import (
    COVERAGE_OPERATION_OUTCOME_DISAGNOSTICS,
    COVERAGE_READ_SCHEMA,
    COVERAGE_READ_SCHEMA_V2,
    COVERAGE_SEARCH_SCHEMA,
    EOB_READ_INPT_SCHEMA,
    EOB_READ_SCHEMA,
    EOB_SEARCH_SCHEMA,
    FHIR_META_SCHEMA,
    FHIR_RES_TYPE_COVERAGE,
    INVALID_COVERAGE_ID,
    INVALID_ID_OPERATION_OUTCOME_DIAGNOSTICS,
    INVALID_PATIENT_ID,
    PATIENT_READ_SCHEMA,
    PATIENT_SEARCH_SCHEMA,
    SAMPLE_A_888_HICN_HASH,
    SAMPLE_A_888_MBI,
    USERINFO_SCHEMA,
    V3_403_DETAIL,
)
from apps.test import BaseApiTest
from apps.testclient.utils import extract_last_page_index
from apps.versions import Versions


class ContainerizedFhirApiIntegrationTests(BaseApiTest):
    """
    Refactored integration tests using standard Django test runner against
    the containerized BFD backend.
    """

    def setUp(self):
        call_command('create_blue_button_scopes')
        self.read_capability = self._create_capability('Read', [])
        self.write_capability = self._create_capability('Write', [])
        super().setUp()

    def _get_fhir_url(self, resource_name, params=None, version=Versions.V2):
        endpoint_url = '/v{}/fhir/{}'.format(version, resource_name)
        if params is not None:
            endpoint_url = '{}/{}'.format(endpoint_url, params)
        return endpoint_url

    def _setup_apiclient(self, fn='John', ln='Doe', fhir_id_v2=None, fhir_id_v3=None, hicn_hash=None, mbi=None):
        access_token = self.create_token(fn, ln, fhir_id_v2, fhir_id_v3, hicn_hash, mbi)

        # Overwrite standard client with DRF's APIClient
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        return access_token

    def _assertHasC4BBProfile(self, resource, c4bb_profile, version):
        meta_profile = None
        try:
            meta_profile = resource['meta']['profile'][0]
        except KeyError:
            pass
        if version is not Versions.V2:
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

    def _assertHasC4BBIdentifier(self, resource, c4bb_type, version):
        identifiers = resource.get('identifier', None)
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

        if version is Versions.V2:
            self.assertTrue(hasC4BB)
        else:
            self.assertFalse(hasC4BB)

    def _extract_urls(self, relations):
        nav_info = {}
        for r in relations:
            nav_info[r.get('relation')] = r.get('url', None)
        return nav_info

    def _get_total_page(self, content):
        total_page = -1
        links = content.get('link', None)
        if links:
            nav_info = self._extract_urls(links)
            total_page = extract_last_page_index(nav_info['last'])
        return total_page

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

    @tag('integration')
    def test_health_endpoint(self):
        """Test that checks the /health endpoint returns a HTTPStatus.OK"""
        response = self.client.get('/health')

        self.assertEqual(response.status_code, HTTPStatus.OK)

        content = response.json()

        self.assertEqual(content.get('message'), "all's well")

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_userinfo_endpoint(self):
        self._call_userinfo_endpoint(Versions.V1)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_userinfo_endpoint_v2(self):
        self._call_userinfo_endpoint(Versions.V2)

    def _call_userinfo_endpoint(self, version):
        """Calling the userinfo endpoint which requires authentication

        Args:
            v2 (bool, optional): If this is a v1 or v2 call. Defaults to False.
        """
        url = '/{}/connect/userinfo'.format('v2' if version is Versions.V2 else 'v1')

        # 1. Unathenticated
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 2. Test authenticated request
        self._setup_apiclient()
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        content = response.json()
        self.assertEqual(validate_json_schema(USERINFO_SCHEMA, content), True)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_fhir_meta_endpoint(self):
        self._call_fhir_meta_endpoint(Versions.V1)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_fhir_meta_endpoint_v2(self):
        self._call_fhir_meta_endpoint(Versions.V2)

    def _call_fhir_meta_endpoint(self, version):
        # 1. Test unauthenticated request, no auth needed for capabilities
        response = self.client.get(self._get_fhir_url('metadata', None, version))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Authenticate
        self._setup_apiclient()

        # 2. Test authenticated request
        response = self.client.get(self._get_fhir_url('metadata', None, version))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Validate JSON Schema
        content = response.json()
        fhir_ver = None
        try:
            fhir_ver = content['fhirVersion']
        except KeyError:
            pass
        self.assertIsNotNone(fhir_ver)
        # match any FHIR ver 4.0.*
        versionOK = fhir_ver and fhir_ver.startswith('4.0.' if version is Versions.V2 else '3.0.2')
        self.assertTrue(versionOK)
        self.assertEqual(validate_json_schema(FHIR_META_SCHEMA, content), True)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_patient_endpoint(self):
        self._call_patient_endpoint(Versions.V1)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_patient_endpoint_v2(self):
        self._call_patient_endpoint(Versions.V2)

    def _call_patient_endpoint(self, version):
        # 1. Test unauthenticated request
        url = self._get_fhir_url(FHIR_RES_TYPE_PATIENT, None, version)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

        # Authenticate
        self._setup_apiclient(fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        # 2. Test SEARCH VIEW endpoint
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        content = response.json()

        self.assertTrue(validate_json_schema(PATIENT_SEARCH_SCHEMA, content))

        for r in content.get('entry', []):
            resource = r['resource']
            self._assertHasC4BBProfile(resource, C4BB_PROFILE_URLS['PATIENT'], version)
            self._assertAddressOK(resource)

        # 3. Test READ VIEW endpoint
        read_url = self._get_fhir_url(FHIR_RES_TYPE_PATIENT, DEFAULT_SAMPLE_FHIR_ID_V2, version)
        response = self.client.get(read_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        content = response.json()

        if version is Versions.V1:
            self.assertTrue(validate_json_schema(PATIENT_READ_SCHEMA, content))

        self._assertHasC4BBProfile(content, C4BB_PROFILE_URLS['PATIENT'], version)
        self._assertAddressOK(content)

        # 4. Test unauthorized READ request
        bad_read_url = self._get_fhir_url(FHIR_RES_TYPE_PATIENT, '99999999999999', version)
        response = self.client.get(bad_read_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_coverage_endpoint(self):
        self._call_coverage_endpoint(Versions.V1)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_coverage_endpoint_v2(self):
        self._call_coverage_endpoint(Versions.V2)

    def _call_coverage_endpoint(self, version):
        # 1. Test unauthenticated request
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_COVERAGE, None, version))
        self.assertEqual(response.status_code, 401)

        # Authenticate
        self._setup_apiclient(fhir_id_v2=DEFAULT_SAMPLE_FHIR_ID_V2)

        # 2. Test SEARCH VIEW endpoint
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_COVERAGE, None, version))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        content = response.json()
        # Validate JSON Schema
        self.assertEqual(validate_json_schema(COVERAGE_SEARCH_SCHEMA, content), True)

        # 3. Test READ VIEW endpoint
        response = self.client.get(
            self._get_fhir_url(FHIR_RES_TYPE_COVERAGE, 'part-a-' + DEFAULT_SAMPLE_FHIR_ID_V2, version)
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        content = response.json()
        # Validate JSON Schema
        self._assertHasC4BBProfile(content, C4BB_PROFILE_URLS['COVERAGE'], version)
        self.assertEqual(
            validate_json_schema(COVERAGE_READ_SCHEMA_V2 if version is Versions.V2 else COVERAGE_READ_SCHEMA, content),
            True,
        )

        # 4. Test unauthorized READ request
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_COVERAGE, 'part-a-99999999999999', version))
        self.assertEqual(response.status_code, 404)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_coverage_search_endpoint(self):
        self._call_coverage_search_endpoint(Versions.V1)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_coverage_search_endpoint_v2(self):
        self._call_coverage_search_endpoint(Versions.V2)

    def _call_coverage_search_endpoint(self, version):

        # Authenticate
        self._setup_apiclient()

        # Coverage search endpoint
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_COVERAGE, None, version))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        content = response.json()

        # Validate JSON Schema: bundle with entries and link section with page navigation: first, next, previous, last, self
        self.assertEqual(validate_json_schema(COVERAGE_SEARCH_SCHEMA, content), True)

        total_page = self._get_total_page(content)
        assert total_page >= 0

        expected_resource_stats = {'part-a': 1, 'part-b': 1, 'part-c': 1, 'part-d': 1}
        resource_stats = {'part-a': 0, 'part-b': 0, 'part-c': 0, 'part-d': 0}
        self._stats_resource_by_type(content, resource_stats)

        for i in range(total_page):
            lnk = content.get('link', None)
            self.assertIsNotNone(
                lnk,
                (
                    "Field 'link' expected, containing page navigation urls e.g. 'first', 'next', 'self', 'previous', 'last' "
                ),
            )
            nav_info = self._extract_urls(lnk)
            if nav_info.get('next', None) is not None:
                response = self.client.get(nav_info['next'])
                self.assertEqual(response.status_code, HTTPStatus.OK)
                content = response.json()
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
    @tag('integration')
    def test_eob_search_endpoint(self):
        """
        Search EOB v1, navigate pages and collect stats of different types of claims
        e.g. pde, carrier, outpatient, inpatient, etc.

        Also validate sample A stats - consistent with IG documentation:

        total claim: 70

        carrier: 50
        pde: 10
        inpatient: 4
        outpatient: 6

        """
        self._call_eob_search_endpoint(Versions.V1)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_eob_search_endpoint_v2(self):
        """
        Search EOB v2, navigate pages and collect stats of different types of claims
        e.g. pde, carrier, outpatient, inpatient, etc.
        """
        self._call_eob_search_endpoint(Versions.V2)

    def _call_eob_search_endpoint(self, version):

        # Authenticate
        self._setup_apiclient()
        # EOB search endpoint
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, None, version))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        content = response.json()

        # Validate JSON Schema: bundle with entries and link section with page navigation: first, next, previous, last, self
        self.assertEqual(validate_json_schema(EOB_SEARCH_SCHEMA, content), True)

        total_page = self._get_total_page(content)
        assert total_page >= 0

        expected_resource_stats = {'pde': 5, 'carrier': 25, 'inpatient': 0, 'outpatient': 0}
        resource_stats = {'pde': 0, 'carrier': 0, 'inpatient': 0, 'outpatient': 0}
        self._stats_resource_by_type(content, resource_stats)

        # Loop through pages
        for i in range(total_page):
            lnk = content.get('link', None)
            self.assertIsNotNone(
                lnk,
                (
                    "Field 'link' expected, containing page navigation urls e.g. 'first', 'next', 'self', 'previous', 'last' "
                ),
            )
            nav_info = self._extract_urls(lnk)
            if nav_info.get('next', None) is not None:
                response = self.client.get(nav_info['next'])
                self.assertEqual(response.status_code, 200)
                content = response.json()
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
    @tag('integration')
    def test_eob_profiles_endpoint(self):
        # Authenticate
        self._setup_apiclient(
            'sample_a_88888888888888',
            'sample_a_88888888888888',
            '-88888888888888',
            hicn_hash=SAMPLE_A_888_HICN_HASH,
            mbi=SAMPLE_A_888_MBI,
        )

        # EOB search endpoint
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, version=Versions.V2))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        content = response.json()
        # dump_content(json.dumps(content), "eob_search_profiles_888888888888.json")

        # Validate JSON Schema: bundle with entries and link section with page navigation: first, next, previous, last, self
        # comment out since the C4BB EOB resources do not validate with FHIR R4 json schema
        self.assertEqual(validate_json_schema(EOB_SEARCH_SCHEMA, content), True)

        total_page = self._get_total_page(content)
        assert total_page >= 0

        expected_resource_stats = {
            'pde': 1,
            'carrier': 1,
            'inpatient': 1,
            'outpatient': 1,
            'dme': 1,
            'snf': 1,
            'hha': 1,
            'hospice': 1,
        }
        resource_stats = {
            'pde': 0,
            'carrier': 0,
            'inpatient': 0,
            'outpatient': 0,
            'dme': 0,
            'snf': 0,
            'hha': 0,
            'hospice': 0,
        }
        self._stats_resource_by_type(content, resource_stats)

        for i in range(total_page):
            lnk = content.get('link', None)
            self.assertIsNotNone(lnk, "Field 'link' expected...")
            nav_info = self._extract_urls(lnk)

            if nav_info.get('next') is not None:
                # Strip the domain to make it a relative path for self.client
                parsed = urlparse(nav_info['next'])
                relative_next_url = f'{parsed.path}?{parsed.query}'

                response = self.client.get(relative_next_url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                content = response.json()
                self._stats_resource_by_type(content, resource_stats)
            else:
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
    @tag('integration')
    def test_eob_endpoint(self):
        """
        Search and read EOB v1
        """
        self._call_eob_endpoint(Versions.V1)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_eob_endpoint_v2(self):
        """
        Search and read EOB v2
        """
        self._call_eob_endpoint(Versions.V2)

    def _call_eob_endpoint(self, version):

        # 1. Test unauthenticated request
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, None, version))
        self.assertEqual(response.status_code, 401)

        # Authenticate
        self._setup_apiclient()

        # 2. Test SEARCH VIEW endpoint, default to current bene's PDE
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, None, version))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        content = response.json()
        self.assertEqual(validate_json_schema(EOB_SEARCH_SCHEMA, content), True)
        # Validate JSON Schema
        for r in content['entry']:
            self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['NONCLINICIAN'], version)

        # 3. Test READ VIEW endpoint v1 (carrier) and v2
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, 'carrier--22639159481', version))
        content = response.json()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        if version is not Versions.V2:
            # Validate JSON Schema
            self.assertEqual(validate_json_schema(EOB_READ_SCHEMA, content), True)
        self._assertHasC4BBProfile(content, C4BB_PROFILE_URLS['NONCLINICIAN'], version)

        # 4. Test SEARCH VIEW endpoint v1 and v2 (BB2-418 EOB V2 PDE profile)
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, '?patient=-20140000008325', version))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Validate JSON Schema
        content = response.json()
        self.assertEqual(validate_json_schema(EOB_SEARCH_SCHEMA, content), True)
        for r in content['entry']:
            self._assertHasC4BBProfile(r['resource'], C4BB_PROFILE_URLS['NONCLINICIAN'], version)

        # 5. Test unauthorized READ request
        # same asserts for v1 and v2
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, 'carrier--23017401521', version))
        self.assertEqual(response.status_code, 404)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_eob_endpoint_pde(self):
        """
        EOB pde (pharmacy) profile v1
        """
        self._call_eob_endpoint_pde(Versions.V1)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_eob_endpoint_pde_v2(self):
        """
        EOB pde (pharmacy) profile v2
        """
        self._call_eob_endpoint_pde(Versions.V2)

    def _call_eob_endpoint_pde(self, version):

        # Authenticate
        self._setup_apiclient()
        # read eob pde profile v1 and v2
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, 'pde--4894712975', version))
        content = response.json()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        if not version == Versions.V2:
            self.assertEqual(validate_json_schema(EOB_READ_INPT_SCHEMA, content), True)
        self._assertHasC4BBProfile(content, C4BB_PROFILE_URLS['PHARMACY'], version)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_eob_endpoint_inpatient(self):
        self._call_eob_endpoint_inpatient(Versions.V1)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_eob_endpoint_inpatient_v2(self):
        self._call_eob_endpoint_inpatient(Versions.V2)

    def _call_eob_endpoint_inpatient(self, version):

        # Authenticate
        self._setup_apiclient()
        # Test READ VIEW endpoint v1 and v2: inpatient
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, 'inpatient--4436342082', version))
        content = response.json()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        if version == Versions.V2:
            # Validate JSON Schema v1
            self.assertEqual(validate_json_schema(EOB_READ_INPT_SCHEMA, content), True)
        self._assertHasC4BBProfile(content, C4BB_PROFILE_URLS['INPATIENT'], version)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_eob_endpoint_outpatient(self):
        self._call_eob_endpoint_outpatient(Versions.V1)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_eob_endpoint_outpatient_v2(self):
        self._call_eob_endpoint_outpatient(Versions.V2)

    def _call_eob_endpoint_outpatient(self, version):

        # Authenticate
        self._setup_apiclient()
        # Test READ VIEW endpoint v1 and v2: outpatient
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_EOB, 'outpatient--4412920419', version))
        content = response.json()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        if not version == Versions.V2:
            # Validate JSON Schema v1
            self.assertEqual(validate_json_schema(EOB_READ_INPT_SCHEMA, content), True)
        else:
            self.assertEqual(response.status_code, HTTPStatus.OK)
        self._assertHasC4BBProfile(content, C4BB_PROFILE_URLS['OUTPATIENT'], version)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_err_response_caused_by_illegalarguments(self):
        self._err_response_caused_by_illegalarguments(Versions.V1)

    @override_switch('require-scopes', active=True)
    @tag('integration')
    def test_err_response_caused_by_illegalarguments_v2(self):
        self._err_response_caused_by_illegalarguments(Versions.V2)

    def _err_response_caused_by_illegalarguments(self, version):

        # Authenticate
        self._setup_apiclient()
        response = self.client.get(self._get_fhir_url(FHIR_RES_TYPE_COVERAGE, 'part-d___--20140000008325', version))
        # This now returns 400 after BB2-2063 work.
        # for both v1 and v2
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    @override_switch('v3_endpoints', active=True)
    @tag('integration')
    def test_patient_read_endpoint_v3_403(self):
        """
        test patient read v3 throwing a 403 when an app is not in the flag
        TODO - Should be removed when v3_early_adopter flag is deleted and v3 is available for all apps
        """
        self._call_v3_endpoint_to_assert_403(FHIR_RES_TYPE_PATIENT, DEFAULT_SAMPLE_FHIR_ID_V3, False, '')

    @override_switch('v3_endpoints', active=True)
    @tag('integration')
    def test_coverage_read_endpoint_v3_403(self):
        """
        test coverage read v3 throwing a 403 when an app is not in the flag
        TODO - Should be removed when v3_early_adopter flag is deleted and v3 is available for all apps
        """
        self._call_v3_endpoint_to_assert_403(FHIR_RES_TYPE_COVERAGE, 'part-a-99999999999999', False, '')

    @override_switch('v3_endpoints', active=True)
    @tag('integration')
    def test_eob_read_endpoint_v3_403(self):
        """
        test eob read v3 throwing a 403 when an app is not in the flag
        TODO - Should be removed when v3_early_adopter flag is deleted and v3 is available for all apps
        """
        self._call_v3_endpoint_to_assert_403(FHIR_RES_TYPE_EOB, 'outpatient--9999999999999', False, '')

    @override_switch('v3_endpoints', active=True)
    @tag('integration')
    def test_patient_search_endpoint_v3_403(self):
        """
        test patient search v3 throwing a 403 when an app is not in the flag
        TODO - Should be removed when v3_early_adopter flag is deleted and v3 is available for all apps
        """
        self._call_v3_endpoint_to_assert_403(FHIR_RES_TYPE_PATIENT, DEFAULT_SAMPLE_FHIR_ID_V3, True, '_id=')

    @override_switch('v3_endpoints', active=True)
    @tag('integration')
    def test_coverage_search_endpoint_v3_403(self):
        """
        test coverage search v3 throwing a 403 when an app is not in the flag
        TODO - Should be removed when v3_early_adopter flag is deleted and v3 is available for all apps
        """
        self._call_v3_endpoint_to_assert_403(FHIR_RES_TYPE_COVERAGE, DEFAULT_SAMPLE_FHIR_ID_V3, True, 'beneficiary=')

    @override_switch('v3_endpoints', active=True)
    @tag('integration')
    def test_eob_search_endpoint_v3_403(self):
        """
        test eob search v3 throwing a 403 when an app is not in the flag
        TODO - Should be removed when v3_early_adopter flag is deleted and v3 is available for all apps
        """
        self._call_v3_endpoint_to_assert_403(FHIR_RES_TYPE_EOB, DEFAULT_SAMPLE_FHIR_ID_V3, True, 'patient=')

    def _call_v3_endpoint_to_assert_403(
        self, resource_type: str, resource_value: str, is_search_call: bool, search_param: str
    ):

        # Authenticate
        self._setup_apiclient(fhir_id_v3=DEFAULT_SAMPLE_FHIR_ID_V3)
        Flag.objects.create(name='v3_early_adopter', everyone=None)
        if is_search_call:
            endpoint_url = self._get_fhir_url(resource_type, f'?{search_param}{resource_value}', Versions.V3)
        else:
            endpoint_url = self._get_fhir_url(resource_type, f'{search_param}{resource_value}', Versions.V3)
        response = self.client.get(endpoint_url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json()['detail'], V3_403_DETAIL)

    @override_switch('v3_endpoints', active=True)
    @tag('integration')
    def test_patient_search_endpoint_v3_400_operation_outcome(self):
        """
        test patient search v3 throwing a 400 operation outcome when a bad request is made
        """
        self._call_v3_endpoint(
            FHIR_RES_TYPE_PATIENT,
            INVALID_PATIENT_ID,
            True,
            '_id=',
            INVALID_ID_OPERATION_OUTCOME_DIAGNOSTICS,
        )

    @override_switch('v3_endpoints', active=True)
    @tag('integration')
    def test_patient_read_endpoint_v3_400_operation_outcome(self):
        """
        test patient read v3 throwing a 400 operation outcome when a bad request is made
        """
        self._call_v3_endpoint(
            FHIR_RES_TYPE_PATIENT,
            INVALID_PATIENT_ID,
            False,
            '',
            INVALID_ID_OPERATION_OUTCOME_DIAGNOSTICS,
        )

    @override_switch('v3_endpoints', active=True)
    @tag('integration')
    def test_eob_read_endpoint_v3_400_operation_outcome(self):
        """
        test EOB read v3 throwing a 400 operation outcome when a bad request is made
        """
        self._call_v3_endpoint(
            FHIR_RES_TYPE_EOB,
            INVALID_PATIENT_ID,
            False,
            '',
            INVALID_ID_OPERATION_OUTCOME_DIAGNOSTICS,
        )

    @override_switch('v3_endpoints', active=True)
    @tag('integration')
    def test_coverage_read_endpoint_v3_400_operation_outcome(self):
        """
        test coverage read v3 throwing a 400 operation outcome when a bad request is made
        """
        self._call_v3_endpoint(
            FHIR_RES_TYPE_COVERAGE,
            INVALID_COVERAGE_ID,
            False,
            '',
            COVERAGE_OPERATION_OUTCOME_DISAGNOSTICS,
        )

    def _call_v3_endpoint(
        self, resource_type: str, resource_value: str, is_search_call: bool, search_param: str, diagnostics_result: str
    ):

        # Authenticate
        self._setup_apiclient()
        # Ensure we don't get a 403 on the v3 call
        Flag.objects.create(name='v3_early_adopter', everyone=True)
        if is_search_call:
            endpoint_url = self._get_fhir_url(resource_type, f'?{search_param}{resource_value}', Versions.V3)
        else:
            endpoint_url = self._get_fhir_url(resource_type, f'{search_param}{resource_value}', Versions.V3)
        response = self.client.get(endpoint_url)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(response.json()['resourceType'], OPERATION_OUTCOME)
        self.assertEqual(response.json()['issue'][0]['severity'], 'error')
        self.assertEqual(response.json()['issue'][0]['code'], 'processing')
        self.assertEqual(response.json()['issue'][0]['diagnostics'], diagnostics_result)
