from unittest.mock import patch
import json
from httmock import all_requests, HTTMock, urlmatch
from apps.mymedicare_cb.tests.responses import patient_response
import apps.fhir.bluebutton.utils
import apps.fhir.bluebutton.views.home
from apps.fhir.bluebutton.views.home import (conformance_filter)
from django.test import TestCase, RequestFactory
from apps.test import BaseApiTest
from django.test.client import Client
from django.core.urlresolvers import reverse

# Get the pre-defined Conformance statement
from .data_conformance import CONFORMANCE


class ConformanceReadRequestTest(TestCase):
    """ Check the BlueButton API call  """

    # 'fhir_server_testdata_prep.json',
    fixtures = ['fhir_bluebutton_test_rt.json']

    def setUp(self):
        # Setup the RequestFactory
        self.factory = RequestFactory()
        self.client = Client()

    @patch('apps.fhir.bluebutton.utils.requests')
    def test_fhir_bluebutton_read_conformance_testcase(self, mock_requests):
        """ Checking Conformance

            The @patch replaces the call to requests with mock_requests

        """

        call_to = '/bluebutton/fhir/v1/metadata'
        request = self.factory.get(call_to)

        # Now we can setup the responses we want to the call
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.content = CONFORMANCE

        # Make the call to request_call which uses requests.get
        # patch will intercept the call to requests.get and
        # return the pre-defined values
        result = apps.fhir.bluebutton.utils.request_call(request,
                                                         call_to,
                                                         crosswalk=None)

        # Test for a match
        self.assertEqual(result._response.content, CONFORMANCE)

    @patch('apps.fhir.bluebutton.views.home.get_resource_names')
    def test_fhir_conformance_filter(self, mock_get_resource_names):
        """ Check filtering of Conformance Statement """

        # Now we can setup the responses we want to the call
        mock_get_resource_names.return_value = ['ExplanationOfBenefit',
                                                'Patient']

        conform_out = json.loads(CONFORMANCE)
        result = conformance_filter(conform_out, None)

        if "vision" in result['rest'][0]['resource']:
            filter_works = False
        else:
            filter_works = True

        self.assertEqual(filter_works, True)


class ThrottleReadRequestTest(BaseApiTest):

    fixtures = ['testfixture']

    def setUp(self):
        # create read and write capabilities
        self.read_capability = self._create_capability('Read', [])
        self.write_capability = self._create_capability('Write', [])
        # Setup the RequestFactory
        self.client = Client()

    @patch('apps.dot_ext.throttling.TokenRateThrottle.get_rate')
    def test_read_throttle(self,
                           mock_rates):
        mock_rates.return_value = '1/day'
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content':{"resourceType":"Patient","id":"20140000008325","extension":[{"url":"https://bluebutton.cms.gov/resources/variables/race","valueCoding":{"system":"https://bluebutton.cms.gov/resources/variables/race","code":"1","display":"White"}}],"identifier":[{"system":"https://bluebutton.cms.gov/resources/variables/bene_id","value":"20140000008325"},{"system":"https://bluebutton.cms.gov/resources/identifier/hicn-hash","value":"2025fbc612a884853f0c245e686780bf748e5652360ecd7430575491f4e018c5"}],"name":[{"use":"usual","family":"Doe","given":["Jane","X"]}],"gender":"unknown","birthDate":"2014-06-01","address":[{"district":"999","state":"15","postalCode":"99999"}]} # noqa
            }

        with HTTMock(catchall):

            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_read_or_update_or_delete',
                    kwargs={
                        'resource_type': 'Patient',
                        'resource_id': 20140000008325}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 200)

            self.assertTrue(response.has_header("X-RateLimit-Limit"))
            self.assertEqual(response.get("X-RateLimit-Limit"), "1")

            self.assertTrue(response.has_header("X-RateLimit-Remaining"))
            self.assertEqual(response.get("X-RateLimit-Remaining"), "0")

            self.assertTrue(response.has_header("X-RateLimit-Reset"))
            # 86400.0 is 24 hours
            self.assertEqual(response.get("X-RateLimit-Reset"), '86400.0')

            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_read_or_update_or_delete',
                    kwargs={
                        'resource_type': 'Patient',
                        'resource_id': 20140000008325}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 429)
            # Assert that the proper headers are in place
            self.assertTrue(response.has_header("X-RateLimit-Limit"))
            self.assertEqual(response.get("X-RateLimit-Limit"), "1")

            self.assertTrue(response.has_header("X-RateLimit-Remaining"))
            self.assertEqual(response.get("X-RateLimit-Remaining"), "0")

            self.assertTrue(response.has_header("X-RateLimit-Reset"))
            # 86400.0 is 24 hours
            self.assertTrue(float(response.get("X-RateLimit-Reset")) < 86400.0)

            self.assertTrue(response.has_header("Retry-After"))
            self.assertEqual(response.get("Retry-After"), "86400")

            # Assert that the search endpoint is also ratelimited
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_search',
                    kwargs={
                        'resource_type': 'Patient'}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 429)

            # Assert that another token is not rate limited
            second_access_token = self.create_token('Bob', 'Bobbington')
            self.assertFalse(second_access_token == first_access_token)

            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_read_or_update_or_delete',
                    kwargs={
                        'resource_type': 'Patient',
                        'resource_id': 20140000008325}),
                Authorization="Bearer %s" % (second_access_token))

            self.assertEqual(response.status_code, 200)


class BackendConnectionTest(BaseApiTest):

    fixtures = ['testfixture']

    def setUp(self):
        # create read and write capabilities
        self.read_capability = self._create_capability('Read', [])
        self.write_capability = self._create_capability('Write', [])
        # Setup the RequestFactory
        self.client = Client()

    def test_search_request(self):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        expected_request = {
            'method': 'GET',
            'url': ("https://fhir.backend.bluebutton.hhsdevcloud.us/"
                    "baseDstu3/Patient/?_format=application%2Fjson%2Bfhir&_id=20140000008325"),
            'headers': {
                'User-Agent': 'python-requests/2.18.4',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'Connection': 'keep-alive',
                'BlueButton-OriginalQueryCounter': '1',
                'BlueButton-BeneficiaryId': 'patientId:20140000008325',
                'BlueButton-Application': 'John_Smith_test',
                'BlueButton-OriginatingIpAddress': '127.0.0.1',
                'keep-alive': 'timeout=120, max=10',
                'BlueButton-OriginalUrl': '/v1/fhir/Patient',
                'BlueButton-BackendCall': 'https://fhir.backend.bluebutton.hhsdevcloud.us/baseDstu3/Patient/',
            }
        }

        expected_response = {
            "resourceType": "Bundle",
            "id": "d0c10556-a3df-4af6-bdb3-d60908b1f16b",
            "meta": {
                "lastUpdated": "2018-04-05T15:44:17.721-04:00"
            },
            "type": "searchset",
            "total": 1,
            "link": [{
                "url": ("http://testserver/v1/fhir/Patient/"
                        "?_format=application%2Fjson%2Bfhir&_id=20140000008325&count=10&startIndex=0"),
                "relation": "self"
            }],
            "entry": [{
                "fullUrl": "https://sandbox.bluebutton.cms.gov/v1/fhir/Patient/19990000000001",
                "resource": {
                    "resourceType": "Patient",
                    "id": "19990000000001",
                    "extension": [{
                        "url": "https://bluebutton.cms.gov/resources/variables/race",
                        "valueCoding": {
                            "system": "https://bluebutton.cms.gov/resources/variables/race",
                            "code": "1",
                            "display": "White"
                        }
                    }],
                    "identifier": [{
                        "system": "https://bluebutton.cms.gov/resources/variables/bene_id",
                        "value": "19990000000001"
                    }, {
                        "system": "https://bluebutton.cms.gov/resources/identifier/hicn-hash",
                        "value": "96228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7"
                    }],
                    "name": [{
                        "use": "usual",
                        "family": "Doe",
                        "given": [
                            "Jane",
                            "X"
                        ]
                    }],
                    "gender": "unknown",
                    "birthDate": "1999-06-01",
                    "address": [{
                        "district": "999",
                        "state": "30",
                        "postalCode": "99999"
                    }]
                }
            }]
        }

        @all_requests
        def catchall(url, req):
            self.assertIn("https://fhir.backend.bluebutton.hhsdevcloud.us/baseDstu3/Patient/", req.url)
            self.assertIn("_format=application%2Fjson%2Bfhir", req.url)
            self.assertIn("_id=20140000008325", req.url)
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
                    'bb_oauth_fhir_search',
                    kwargs={'resource_type': 'Patient'}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['entry'], expected_response['entry'])
            self.assertTrue(len(response.json()['link']) > 0)

    def test_search_request_unauthorized(self):
        response = self.client.get(
            reverse(
                'bb_oauth_fhir_search',
                kwargs={'resource_type': 'Patient'}),
            Authorization="Bearer bogus")

        self.assertEqual(response.status_code, 401)

    def test_search_request_not_found(self):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        expected_request = {
            'method': 'GET',
            'url': ("https://fhir.backend.bluebutton.hhsdevcloud.us/"
                    "baseDstu3/Patient/?_format=application%2Fjson%2Bfhir&_id=20140000008325"),
            'headers': {
                'User-Agent': 'python-requests/2.18.4',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'Connection': 'keep-alive',
                'BlueButton-OriginalQueryCounter': '1',
                'BlueButton-BeneficiaryId': 'patientId:20140000008325',
                'BlueButton-Application': 'John_Smith_test',
                'BlueButton-OriginatingIpAddress': '127.0.0.1',
                'keep-alive': 'timeout=120, max=10',
                'BlueButton-OriginalUrl': '/v1/fhir/Patient',
                'BlueButton-BackendCall': 'https://fhir.backend.bluebutton.hhsdevcloud.us/baseDstu3/Patient/',
            }
        }

        @all_requests
        def catchall(url, req):
            self.assertIn("https://fhir.backend.bluebutton.hhsdevcloud.us/baseDstu3/Patient/", req.url)
            self.assertIn("_format=application%2Fjson%2Bfhir", req.url)
            self.assertIn("_id=20140000008325", req.url)
            self.assertEqual(expected_request['method'], req.method)
            self.assertDictContainsSubset(expected_request['headers'], req.headers)

            return {
                'status_code': 404,
                'content': {},
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_search',
                    kwargs={'resource_type': 'Patient'}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 404)

    def test_search_emptyset(self):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': {
                    "resourceType": "Bundle",
                    "id": "4b74b5b0-f324-41cb-85db-f8d527f79128",
                    "meta": {
                        "lastUpdated": "2018-05-15T14:01:58.603+00:00"
                    },
                    "type": "searchset",
                    "total": 0,
                    "link": [
                        {
                            "relation": "self",
                            "url": "http://hapi.fhir.org/baseDstu3/ExplanationOfBenefit?_pretty=true&patient=1234"
                        },
                    ],
                },
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_search',
                    kwargs={'resource_type': 'ExplanationOfBenefit'}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 200)

    def test_search_request_failed(self):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        expected_request = {
            'method': 'GET',
            'url': ("https://fhir.backend.bluebutton.hhsdevcloud.us/"
                    "baseDstu3/Patient/?_format=application%2Fjson%2Bfhir&_id=20140000008325"),
            'headers': {
                'User-Agent': 'python-requests/2.18.4',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'Connection': 'keep-alive',
                'BlueButton-OriginalQueryCounter': '1',
                'BlueButton-BeneficiaryId': 'patientId:20140000008325',
                'BlueButton-Application': 'John_Smith_test',
                'BlueButton-OriginatingIpAddress': '127.0.0.1',
                'keep-alive': 'timeout=120, max=10',
                'BlueButton-OriginalUrl': '/v1/fhir/Patient',
                'BlueButton-BackendCall': 'https://fhir.backend.bluebutton.hhsdevcloud.us/baseDstu3/Patient/',
            }
        }

        @all_requests
        def catchall(url, req):
            self.assertIn("https://fhir.backend.bluebutton.hhsdevcloud.us/baseDstu3/Patient/", req.url)
            self.assertIn("_format=application%2Fjson%2Bfhir", req.url)
            self.assertIn("_id=20140000008325", req.url)
            self.assertEqual(expected_request['method'], req.method)
            self.assertDictContainsSubset(expected_request['headers'], req.headers)

            return {
                'status_code': 500,
                'content': {},
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_search',
                    kwargs={'resource_type': 'Patient'}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 502)

    def test_search_request_failed_no_fhir_id(self):
        # create the user
        first_access_token = self.create_token_no_fhir('John', 'Smith')

        expected_request = {
            'method': 'GET',
            'url': ("https://fhir.backend.bluebutton.hhsdevcloud.us/"
                    "baseDstu3/Patient/?_format=application%2Fjson%2Bfhir&_id=20140000008325"),
            'headers': {
                'User-Agent': 'python-requests/2.18.4',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'Connection': 'keep-alive',
                'BlueButton-OriginalQueryCounter': '1',
                'BlueButton-BeneficiaryId': 'patientId:20140000008325',
                'BlueButton-Application': 'John_Smith_test',
                'BlueButton-OriginatingIpAddress': '127.0.0.1',
                'keep-alive': 'timeout=120, max=10',
                'BlueButton-OriginalUrl': '/v1/fhir/Patient',
                'BlueButton-BackendCall': 'https://fhir.backend.bluebutton.hhsdevcloud.us/baseDstu3/Patient/',
            }
        }

        @urlmatch(query=r'.*identifier=http%3A%2F%2Fbluebutton.cms.hhs.gov%2Fidentifier%23hicnHash%7C139e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e0dd3f1130.*')  # noqa
        def fhir_request(url, req):
            return {
                'status_code': 200,
                'content': {
                    'total': 1,
                    'entry': [{
                        'resource': {
                            'id': 20140000008325,
                        },
                    }],
                },
            }

        @all_requests
        def catchall(url, req):
            self.assertIn("https://fhir.backend.bluebutton.hhsdevcloud.us/baseDstu3/Patient/", req.url)
            self.assertIn("_format=application%2Fjson%2Bfhir", req.url)
            self.assertIn("_id=20140000008325", req.url)
            self.assertEqual(expected_request['method'], req.method)
            self.assertDictContainsSubset(expected_request['headers'], req.headers)

            return {
                'status_code': 500,
                'content': {},
            }

        with HTTMock(fhir_request, catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_search',
                    kwargs={'resource_type': 'Patient'}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 502)

    def test_read_request_failed_no_fhir_id(self):
        # create the user
        first_access_token = self.create_token_no_fhir('John', 'Smith')

        @urlmatch(query=r'.*identifier=http%3A%2F%2Fbluebutton.cms.hhs.gov%2Fidentifier%23hicnHash%7C139e178537ed3bc486e6a7195a47a82a2cd6f46e911660fe9775f6e0dd3f1130.*')  # noqa
        def fhir_request(url, req):
            return {
                'status_code': 200,
                'content': {
                    'total': 1,
                    'entry': [{
                        'resource': {
                            'id': 20140000008324,
                        },
                    }],
                },
            }

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': {},
            }

        with HTTMock(fhir_request, catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_read_or_update_or_delete',
                    kwargs={'resource_type': 'Patient', 'resource_id': '20140000008325'}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 403)

    def test_read_request(self):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        expected_request = {
            'method': 'GET',
            'url': 'https://fhir.backend.bluebutton.hhsdevcloud.us/baseDstu3/Patient/20140000008325/?_format=json',
            'headers': {
                'User-Agent': 'python-requests/2.18.4',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'Connection': 'keep-alive',
                'BlueButton-OriginalQueryCounter': '1',
                'BlueButton-BeneficiaryId': 'patientId:20140000008325',
                'BlueButton-Application': 'John_Smith_test',
                'BlueButton-OriginatingIpAddress': '127.0.0.1',
                'keep-alive': 'timeout=120, max=10',
                'BlueButton-OriginalUrl': '/v1/fhir/Patient/20140000008325',
                'BlueButton-BackendCall': 'https://fhir.backend.bluebutton.hhsdevcloud.us/baseDstu3/Patient/20140000008325/',
            }
        }

        @all_requests
        def catchall(url, req):
            self.assertEqual(expected_request['url'], req.url)
            self.assertEqual(expected_request['method'], req.method)
            self.assertDictContainsSubset(expected_request['headers'], req.headers)

            return {
                'status_code': 200,
                'content':{"resourceType":"Patient","id":"20140000008325","extension":[{"url":"https://bluebutton.cms.gov/resources/variables/race","valueCoding":{"system":"https://bluebutton.cms.gov/resources/variables/race","code":"1","display":"White"}}],"identifier":[{"system":"https://bluebutton.cms.gov/resources/variables/bene_id","value":"20140000008325"},{"system":"https://bluebutton.cms.gov/resources/identifier/hicn-hash","value":"2025fbc612a884853f0c245e686780bf748e5652360ecd7430575491f4e018c5"}],"name":[{"use":"usual","family":"Doe","given":["Jane","X"]}],"gender":"unknown","birthDate":"2014-06-01","address":[{"district":"999","state":"15","postalCode":"99999"}]} # noqa
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_read_or_update_or_delete',
                    kwargs={'resource_type': 'Patient', 'resource_id': '20140000008325'}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 200)

    def test_read_eob_request(self):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': {
                    'patient': {
                        'reference': 'stuff/20140000008325',
                    },
                },
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_read_or_update_or_delete',
                    kwargs={'resource_type': 'ExplanationOfBenefit', 'resource_id': 'eob_id'}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 200)

    def test_read_coverage_request(self):
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content': {
                    'beneficiary': {
                        'reference': 'stuff/20140000008325',
                    },
                },
            }

        with HTTMock(catchall):
            response = self.client.get(
                reverse(
                    'bb_oauth_fhir_read_or_update_or_delete',
                    kwargs={'resource_type': 'Coverage', 'resource_id': 'coverage_id'}),
                Authorization="Bearer %s" % (first_access_token))

            self.assertEqual(response.status_code, 200)
