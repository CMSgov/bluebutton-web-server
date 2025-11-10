import json

from django.test import RequestFactory
from django.test.client import Client
from httmock import HTTMock, urlmatch
from rest_framework import exceptions
from apps.fhir.bluebutton.exceptions import UpstreamServerException
from apps.test import BaseApiTest
from ..authentication import match_fhir_id
from apps.constants import Versions
from .responses import responses

from hhs_oauth_server.settings.base import MOCK_FHIR_ENDPOINT_HOSTNAME, MOCK_FHIR_V3_ENDPOINT_HOSTNAME


def mock_fhir_url(version):
    return MOCK_FHIR_ENDPOINT_HOSTNAME if version in [1, 2] else MOCK_FHIR_V3_ENDPOINT_HOSTNAME


#     MOCK_FHIR_PATH = "/v1/fhir/Patient/"
def mock_fhir_path(version):
    return f"/v{version}/fhir/Patient"


class TestAuthentication(BaseApiTest):
    MOCK_FHIR_URL = mock_fhir_url(Versions.NOT_AN_API_VERSION)
    MOCK_FHIR_PATH_VERSIONED = mock_fhir_path(Versions.NOT_AN_API_VERSION)
    MOCK_FHIR_HICN_QUERY = ".*hicnHash.*"
    MOCK_FHIR_MBI_QUERY = ".*us-mbi|.*"
    SUCCESS_KEY = 'success'
    NOT_FOUND_KEY = 'not_found'
    ERROR_KEY = 'error'
    DUPLICATES_KEY = 'duplicates'
    LYING_KEY = 'lying'
    MALFORMED_KEY = 'malformed'

    def setUp(self):
        # Setup the RequestFactory
        self.factory = RequestFactory()
        self.client = Client()
        self.request = self.factory.get('http://localhost:8000/mymedicare/sls-callback')
        self.request.session = self.client.session

    # The mock uses data from responses.py. We need to have mock data for a given MBI/FHIR ID
    # for each version of the API we want to test this way. We can use the v2 test data for
    # v3 because we're just asking "do you have a valid us-mbi query string?", and usnig that to then
    # look up the mock response.
    @classmethod
    def create_fhir_mock(cls, hicn_response_key, mbi_response_key, version=Versions.NOT_AN_API_VERSION):
        @urlmatch(netloc=mock_fhir_url(version), path=mock_fhir_path(version), method='POST')
        def mock_fhir_post(url, request):
            try:
                body = request.body
                identifier = body.split('=', 1)[1]
                if 'hicn-hash' in identifier:
                    return responses[hicn_response_key]
                elif 'us-mbi' in identifier:
                    return responses[mbi_response_key]
                else:
                    raise Exception(f"Invalid identifier: {identifier}")
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse json: {e.msg}")
        return mock_fhir_post

    def test_match_fhir_id_success(self):
        '''
            Testing responses: HICN = success
                               MBI = success
            Expecting: Match via MBI first / hash_lockup_type="M"
        '''
        with HTTMock(self.create_fhir_mock(self.SUCCESS_KEY, self.SUCCESS_KEY, Versions.V2)):
            fhir_id, hash_lookup_type = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash,
                request=self.request,
                version=Versions.V2
            )
            self.assertEqual(fhir_id, '-20000000002346')
            self.assertEqual(hash_lookup_type, 'M')

    def test_match_fhir_id_hicn_success(self):
        '''
            Testing responses: HICN = success
                               MBI = not_found
            Expecting: Match via HICN / hash_lockup_type="H"
        '''
        with HTTMock(self.create_fhir_mock(self.SUCCESS_KEY, self.NOT_FOUND_KEY, Versions.V2)):
            fhir_id, hash_lookup_type = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash,
                request=self.request,
                version=Versions.V2
            )
            self.assertEqual(fhir_id, "-20000000002346")
            self.assertEqual(hash_lookup_type, "H")

    def test_match_fhir_id_mbi_success(self):
        '''
            Testing responses: HICN = not_found
                               MBI = success
            Expecting: Match via MBI / hash_lockup_type="M"
        '''
        with HTTMock(self.create_fhir_mock(self.NOT_FOUND_KEY, self.SUCCESS_KEY, Versions.V2)):
            fhir_id, hash_lookup_type = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)
            self.assertEqual(fhir_id, "-20000000002346")
            self.assertEqual(hash_lookup_type, "M")

    def test_match_fhir_id_not_found(self):
        '''
            Testing responses: HICN = not_found
                               MBI = not_found
            Expecting: NotFound exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.NOT_FOUND_KEY, self.NOT_FOUND_KEY, Versions.V2)):
            with self.assertRaises(exceptions.NotFound):
                fhir_id, hash_lookup_type = match_fhir_id(
                    mbi=self.test_mbi,
                    hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)

    def test_match_fhir_id_server_hicn_error(self):
        '''
            Testing responses: HICN = error
                               MBI = not_found
            Expecting: HTTPError exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.ERROR_KEY, self.NOT_FOUND_KEY, Versions.V2)):
            with self.assertRaises(UpstreamServerException):
                fhir_id, hash_lookup_type = match_fhir_id(
                    mbi=self.test_mbi,
                    hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)

    def test_match_fhir_id_server_mbi_error(self):
        '''
            Testing responses: HICN = not_found
                               MBI = error
            Expecting: HTTPError exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.NOT_FOUND_KEY, self.ERROR_KEY, Versions.V2)):
            with self.assertRaises(UpstreamServerException):
                fhir_id, hash_lookup_type = match_fhir_id(
                    mbi=self.test_mbi,
                    hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)

    def test_match_fhir_id_duplicates_hicn(self):
        '''
            Testing responses: HICN = duplicates
                               MBI = not_found
            Expecting: UpstreamServerException exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.DUPLICATES_KEY, self.NOT_FOUND_KEY, Versions.V2)):
            with self.assertRaisesRegexp(UpstreamServerException, "^Duplicate.*"):
                fhir_id, hash_lookup_type = match_fhir_id(
                    mbi=self.test_mbi,
                    hicn_hash=self.test_hicn_hash, request=self.request)

    def test_match_fhir_id_duplicates_mbi(self):
        '''
            Testing responses: HICN = success
                               MBI = duplicates
            Expecting: UpstreamServerException exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.SUCCESS_KEY, self.DUPLICATES_KEY, Versions.V2)):
            with self.assertRaisesRegexp(UpstreamServerException, "^Duplicate.*"):
                fhir_id, hash_lookup_type = match_fhir_id(
                    mbi=self.test_mbi,
                    hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)

    def test_match_fhir_id_duplicates_both(self):
        '''
            Testing responses: HICN = duplicates
                               MBI = duplicates
            Expecting: UpstreamServerException exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.DUPLICATES_KEY, self.DUPLICATES_KEY, Versions.V2)):
            with self.assertRaisesRegexp(UpstreamServerException, "^Duplicate.*"):
                fhir_id, hash_lookup_type = match_fhir_id(
                    mbi=self.test_mbi,
                    hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)

    def test_match_fhir_id_malformed_hicn(self):
        '''
            Testing responses: HICN = malformed
                               MBI = not_found
            Expecting: UpstreamServerException exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.MALFORMED_KEY, self.NOT_FOUND_KEY, Versions.V2)):
            with self.assertRaisesRegexp(UpstreamServerException, "^Unexpected in Patient search:*"):
                fhir_id, hash_lookup_type = match_fhir_id(
                    mbi=self.test_mbi,
                    hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)

    def test_match_fhir_id_malformed_mbi(self):
        '''
            Testing responses: HICN = success
                               MBI = malformed
            Expecting: UpstreamServerException exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.SUCCESS_KEY, self.MALFORMED_KEY, Versions.V2)):
            with self.assertRaisesRegexp(UpstreamServerException, "^Unexpected in Patient search:*"):
                fhir_id, hash_lookup_type = match_fhir_id(
                    mbi=self.test_mbi,
                    hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)
