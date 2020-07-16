import logging
import re
from io import StringIO
from apps.test import BaseApiTest
from django.test.client import Client
from django.urls import reverse
from httmock import all_requests, HTTMock


class FhirReadAuditLoggerTest(BaseApiTest):
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
        self.token_logger = logging.getLogger('audit.authorization.token')
        self.token_logger.setLevel(logging.INFO)
        self.token_stream = StringIO()
        self.token_ch = logging.StreamHandler(self.token_stream)
        self.token_ch.setLevel(logging.INFO)
        self.token_logger.addHandler(self.token_ch)
        for h in self.token_logger.handlers:
            self.token_logger.removeHandler(h)
        self.token_logger.addHandler(self.token_ch)

        self.sls_logger = logging.getLogger('audit.authorization.sls')
        self.sls_logger.setLevel(logging.INFO)
        self.sls_stream = StringIO()
        self.sls_ch = logging.StreamHandler(self.sls_stream)
        self.sls_ch.setLevel(logging.INFO)
        self.sls_logger.addHandler(self.sls_ch)
        for h in self.sls_logger.handlers:
            self.sls_logger.removeHandler(h)
        self.sls_logger.addHandler(self.sls_ch)

        self.fhir_logger = logging.getLogger('audit.data.fhir')
        self.fhir_logger.setLevel(logging.INFO)
        self.fhir_stream = StringIO()
        self.fhir_ch = logging.StreamHandler(self.fhir_stream)
        self.fhir_ch.setLevel(logging.INFO)
        self.fhir_logger.addHandler(self.fhir_ch)
        for h in self.fhir_logger.handlers:
            self.fhir_logger.removeHandler(h)
        self.fhir_logger.addHandler(self.fhir_ch)

    def tearDown(self):
        # tear down token logger
        self.token_logger.removeHandler(self.token_ch)
        del self.token_logger, self.token_ch, self.token_stream
        # tear down sls logger
        self.sls_logger.removeHandler(self.sls_ch)
        del self.sls_logger, self.sls_ch, self.sls_stream
        # tear down fhir logger
        self.fhir_logger.removeHandler(self.fhir_ch)
        del self.fhir_logger, self.fhir_ch, self.fhir_stream

    def test_fhir_read_audit_logging(self):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        expected_request = {
            'method': 'GET',
            'url': 'https://fhir.backend.bluebutton.hhsdevcloud.us/v1/fhir/Patient/-20140000008325/?_format=json',
            'headers': {
                'User-Agent': 'python-requests/2.20.0',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'Connection': 'keep-alive',
                'BlueButton-OriginalQueryCounter': '1',
                'BlueButton-BeneficiaryId': 'patientId:-20140000008325',
                'BlueButton-Application': 'John_Smith_test',
                'BlueButton-OriginatingIpAddress': '127.0.0.1',
                'keep-alive': 'timeout=120, max=10',
                'BlueButton-OriginalUrl': '/v1/fhir/Patient/-20140000008325',
                'BlueButton-BackendCall': 'https://fhir.backend.bluebutton.hhsdevcloud.us/v1/fhir/Patient/-20140000008325/',
            }
        }

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
                    'bb_oauth_fhir_read_or_update_or_delete',
                    kwargs={'resource_type': 'Patient', 'resource_id': '-20140000008325'}),
                {'hello': 'world'},
                Authorization="Bearer %s" % (first_access_token))
            self.assertEqual(response.status_code, 200)
            log_entries = self.fhir_stream.getvalue()
            log_lines = log_entries.splitlines()
            fhir_data_pattern = '.*"uuid":.*"user":.*"application":.*"path":.*Patient.*'
            has_fhir_data = False
            for line in log_lines:
                if re.match(fhir_data_pattern, line) is not None:
                    has_fhir_data = True
            mesg = 'Expect pattern like "uuid": ... "user": ... "application": ... "path": \
                    "/v1/fhir/Patient/..." in log record, but not found.'
            self.assertTrue(has_fhir_data, mesg)
