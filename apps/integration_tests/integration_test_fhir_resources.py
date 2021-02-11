import json
import jsonschema
from jsonschema import validate

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from oauth2_provider.models import AccessToken
from rest_framework.test import APIClient
from waffle.testutils import override_switch, override_flag

from apps.test import BaseApiTest

from .endpoint_schemas import (FHIR_META_SCHEMA, USERINFO_SCHEMA, PATIENT_READ_SCHEMA, PATIENT_SEARCH_SCHEMA,
                               COVERAGE_READ_SCHEMA, COVERAGE_SEARCH_SCHEMA,
                               EOB_READ_SCHEMA, EOB_SEARCH_SCHEMA)

C4BB_SCHEMAS = {
    "fhir.schema.json": None,
}


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
        schema = open("./apps/integration_tests/fhir_resources_schemas/fhir.schema.json", 'r')
        C4BB_SCHEMAS['fhir.schema.json'] = json.load(schema)
        schema.close()

    def _setup_apiclient(self, client):
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
        first_name = "John"
        last_name = "Doe"
        access_token = base_api_test.create_token(first_name, last_name)

        # Test scope in access_token
        at = AccessToken.objects.get(token=access_token)

        # Setup Bearer token:
        client.credentials(HTTP_AUTHORIZATION="Bearer " + at.token)

    def _validateJsonSchema(self, schema, content):
        try:
            validate(instance=content, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            # Show error info for debugging
            print("jsonschema.exceptions.ValidationError: ", e)
            return False
        return True

    def _assertHasC4BBIdentifier(self, resource, c4bb_type, resource_type, v2=False):
        self.assertEqual(resource['resourceType'], resource_type)
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

    @override_switch('require-scopes', active=True)
    def test_userinfo_endpoint(self):
        self._call_userinfo_endpoint(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
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
        self.assertEqual(self._validateJsonSchema(USERINFO_SCHEMA, content), True)

    @override_switch('require-scopes', active=True)
    def test_fhir_meta_endpoint(self):
        self._call_fhir_meta_endpoint(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
    @override_switch('require-scopes', active=True)
    def test_fhir_meta_endpoint_v2(self):
        self._call_fhir_meta_endpoint(True)

    def _call_fhir_meta_endpoint(self, v2=False):
        base_path = "/{}/fhir/metadata".format('v2' if v2 else 'v1')
        client = APIClient()

        # 1. Test unauthenticated request, no auth needed for capabilities
        url = self.live_server_url + base_path
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

        # Authenticate
        self._setup_apiclient(client)

        # 2. Test authenticated request
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        # Validate JSON Schema
        content = json.loads(response.content)
        fhir_ver = None
        try:
            fhir_ver = content['fhirVersion']
        except KeyError:
            pass
        self.assertIsNotNone(fhir_ver)
        self.assertEqual(fhir_ver, '4.0.0' if v2 else '3.0.2')
        # dump_content(json.dumps(content), "fhir_meta_{}.json".format('v2' if v2 else 'v1'))
        self.assertEqual(self._validateJsonSchema(FHIR_META_SCHEMA, content), True)

    @override_switch('require-scopes', active=True)
    def test_patient_endpoint(self):
        self._call_patient_endpoint(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
    @override_switch('require-scopes', active=True)
    def test_patient_endpoint_v2(self):
        self._call_patient_endpoint(True)

    def _call_patient_endpoint(self, v2=False):
        base_path = "/{}/fhir/Patient".format('v2' if v2 else 'v1')
        client = APIClient()

        # 1. Test unauthenticated request
        url = self.live_server_url + base_path
        response = client.get(url)
        self.assertEqual(response.status_code, 401)

        # Authenticate
        self._setup_apiclient(client)

        # 2. Test SEARCH VIEW endpoint
        url = self.live_server_url + base_path
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        #     Validate JSON Schema
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "patient_search_{}.json".format('v2' if v2 else 'v1'))
        self.assertEqual(self._validateJsonSchema(PATIENT_SEARCH_SCHEMA, content), True)

        for r in content['entry']:
            self._assertHasC4BBIdentifier(r['resource'],
                                          "http://hl7.org/fhir/us/carin-bb/CodeSystem/C4BBIdentifierType",
                                          "Patient", v2)

        # 3. Test READ VIEW endpoint
        url = self.live_server_url + base_path + "/" + settings.DEFAULT_SAMPLE_FHIR_ID
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        #     Validate JSON Schema
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "patient_read_{}.json".format('v2' if v2 else 'v1'))
        self.assertEqual(self._validateJsonSchema(PATIENT_READ_SCHEMA, content), True)

        self._assertHasC4BBIdentifier(content,
                                      "http://hl7.org/fhir/us/carin-bb/CodeSystem/C4BBIdentifierType",
                                      "Patient", v2)

        # 4. Test unauthorized READ request
        url = self.live_server_url + base_path + "/" + "99999999999999"
        response = client.get(url)
        self.assertEqual(response.status_code, 404)

    @override_switch('require-scopes', active=True)
    def test_coverage_endpoint(self):
        self._call_coverage_endpoint(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
    @override_switch('require-scopes', active=True)
    def test_coverage_endpoint_v2(self):
        self._call_coverage_endpoint(True)

    def _call_coverage_endpoint(self, v2=False):
        base_path = "/{}/fhir/Coverage".format('v2' if v2 else 'v1')
        client = APIClient()

        # 1. Test unauthenticated request
        url = self.live_server_url + base_path
        response = client.get(url)
        self.assertEqual(response.status_code, 401)

        # Authenticate
        self._setup_apiclient(client)

        # 2. Test SEARCH VIEW endpoint
        url = self.live_server_url + base_path
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        #     Validate JSON Schema
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "coverage_search_{}.json".format('v2' if v2 else 'v1'))
        self.assertEqual(self._validateJsonSchema(COVERAGE_SEARCH_SCHEMA, content), True)

        # 3. Test READ VIEW endpoint
        url = self.live_server_url + base_path + "/part-a-" + settings.DEFAULT_SAMPLE_FHIR_ID
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        #     Validate JSON Schema
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "coverage_read_{}.json".format('v2' if v2 else 'v1'))

        if not v2:
            self.assertEqual(self._validateJsonSchema(COVERAGE_READ_SCHEMA, content), True)
        else:
            # check C4BB indicator???
            pass

        # 4. Test unauthorized READ request
        url = self.live_server_url + base_path + "/part-a-" + "99999999999999"
        response = client.get(url)
        self.assertEqual(response.status_code, 404)

    @override_switch('require-scopes', active=True)
    def test_eob_endpoint(self):
        self._call_eob_endpoint(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
    @override_switch('require-scopes', active=True)
    def test_eob_endpoint_v2(self):
        self._call_eob_endpoint(True)

    def _call_eob_endpoint(self, v2=False):
        base_path = "/{}/fhir/ExplanationOfBenefit".format('v2' if v2 else 'v1')
        client = APIClient()

        # 1. Test unauthenticated request
        url = self.live_server_url + base_path
        response = client.get(url)
        self.assertEqual(response.status_code, 401)

        # Authenticate
        self._setup_apiclient(client)

        # 2. Test SEARCH VIEW endpoint
        url = self.live_server_url + base_path
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        # Validate JSON Schema
        content = json.loads(response.content)
        # dump_content(json.dumps(content), "eob_search_{}.json".format('v2' if v2 else 'v1'))
        meta_profile = None
        try:
            meta_profile = content['entry'][0]['resource']['meta']['profile'][0]
        except KeyError:
            pass
        if not v2:
            self.assertIsNone(meta_profile)
            self.assertEqual(self._validateJsonSchema(EOB_SEARCH_SCHEMA, content), True)
        else:
            self.assertIsNotNone(meta_profile)
            self.assertEqual(meta_profile,
                             'https://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Pharmacy')
            self.assertEqual(self._validateJsonSchema(EOB_SEARCH_SCHEMA, content), True)

        # 3. Test READ VIEW endpoint v1
        url = self.live_server_url + base_path + "/carrier--22639159481"
        response = client.get(url)
        if not v2:
            self.assertEqual(response.status_code, 200)
            #     Validate JSON Schema
            content = json.loads(response.content)
            # dump_content(json.dumps(content), "eob_read_{}.json".format('v2' if v2 else 'v1'))
            self.assertEqual(self._validateJsonSchema(EOB_READ_SCHEMA, content), True)
        else:
            # not found for now on v2
            self.assertEqual(response.status_code, 404)

        # 4. Test SEARCH VIEW endpoint v2 (BB2-418 EOB V2 PDE profile)
        url = self.live_server_url + base_path + "/?patient=-20140000008325"
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        #     Validate JSON Schema
        content = json.loads(response.content)
        dump_content(json.dumps(content), "eob_search_pt_{}.json".format('v2' if v2 else 'v1'))
        meta_profile = None
        try:
            meta_profile = content['entry'][0]['resource']['meta']['profile'][0]
        except KeyError:
            pass

        if not v2:
            self.assertIsNone(meta_profile)
            self.assertEqual(self._validateJsonSchema(EOB_SEARCH_SCHEMA, content), True)
        else:
            self.assertIsNotNone(meta_profile)
            self.assertEqual(meta_profile,
                             'https://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-ExplanationOfBenefit-Pharmacy')
            self.assertEqual(self._validateJsonSchema(EOB_SEARCH_SCHEMA, content), True)
            # resources = content['entry']
            # self.assertIsNotNone(resources)
            # eob_schema = C4BB_SCHEMAS['fhir.schema.json']['definitions']['ExplanationOfBenefit']
            # for r in resources:
            #     self.assertEqual(self._validateJsonSchema(eob_schema, r), True)

        # 5. Test unauthorized READ request
        # same asserts for v1 and v2
        url = self.live_server_url + base_path + "/carrier-23017401521"
        response = client.get(url)
        self.assertEqual(response.status_code, 404)

    @override_switch('require-scopes', active=True)
    def test_err_response_caused_by_illegalarguments(self):
        self._err_response_caused_by_illegalarguments(False)

    @override_switch('bfd_v2', active=True)
    @override_flag('bfd_v2_flag', active=True)
    @override_switch('require-scopes', active=True)
    def test_err_response_caused_by_illegalarguments_v2(self):
        self._err_response_caused_by_illegalarguments(True)

    def _err_response_caused_by_illegalarguments(self, v2=False):
        base_path = "/{}/fhir/Coverage/part-d___--20140000008325".format('v2' if v2 else 'v1')
        client = APIClient()

        # Authenticate
        self._setup_apiclient(client)

        url = self.live_server_url + base_path
        response = client.get(url)
        # check that bfd error response 500 with root cause 'IllegalArgument'
        # mapped to 400 bad request (client error)
        # for both v1 and v2
        self.assertEqual(response.status_code, 400)
