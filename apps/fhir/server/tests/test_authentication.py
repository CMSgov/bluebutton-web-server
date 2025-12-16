import json

from django.test import RequestFactory
from django.test.client import Client
from httmock import HTTMock, urlmatch
from apps.test import BaseApiTest
from apps.fhir.server.authentication import match_fhir_id, MatchFhirIdErrorType, MatchFhirIdLookupType
from apps.versions import Versions
from apps.fhir.server.tests.responses import responses

from hhs_oauth_server.settings.base import MOCK_FHIR_ENDPOINT_HOSTNAME, MOCK_FHIR_V3_ENDPOINT_HOSTNAME


def mock_fhir_url(version):
    return MOCK_FHIR_ENDPOINT_HOSTNAME if version in [1, 2] else MOCK_FHIR_V3_ENDPOINT_HOSTNAME


def mock_fhir_path(version):
    return f'/v{version}/fhir/Patient'


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

    # The mock uses data from responses.py
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
            Expecting: Match via MBI first / hash_lockup_type=MatchFhirIdLookupType.MBI
        '''
        with HTTMock(self.create_fhir_mock(self.SUCCESS_KEY, self.SUCCESS_KEY, Versions.V2)):
            match_fhir_id_result = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash,
                request=self.request,
                version=Versions.V2
            )
            self.assertEqual(match_fhir_id_result.fhir_id, '-20000000002346')
            self.assertEqual(match_fhir_id_result.lookup_type, MatchFhirIdLookupType.MBI)

    def test_match_fhir_id_hicn_success(self):
        '''
            Testing responses: HICN = success
                               MBI = not_found
            Expecting: Match via HICN / hash_lockup_type=MatchFhirIdLookupType.HICN_HASH
        '''
        with HTTMock(self.create_fhir_mock(self.SUCCESS_KEY, self.NOT_FOUND_KEY, Versions.V2)):
            match_fhir_id_result = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash,
                request=self.request,
                version=Versions.V2
            )
            self.assertEqual(match_fhir_id_result.fhir_id, "-20000000002346")
            self.assertEqual(match_fhir_id_result.lookup_type, MatchFhirIdLookupType.HICN_HASH)

    def test_match_fhir_id_mbi_success(self):
        '''
            Testing responses: HICN = not_found
                               MBI = success
            Expecting: Match via MBI / hash_lockup_type=MatchFhirIdLookupType.MBI
        '''
        with HTTMock(self.create_fhir_mock(self.NOT_FOUND_KEY, self.SUCCESS_KEY, Versions.V2)):
            match_fhir_id_result = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)
            self.assertEqual(match_fhir_id_result.fhir_id, "-20000000002346")
            self.assertEqual(match_fhir_id_result.lookup_type, MatchFhirIdLookupType.MBI)

    def test_match_fhir_id_not_found(self):
        '''
            Testing responses: HICN = not_found
                               MBI = not_found
            Expecting: NotFound exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.NOT_FOUND_KEY, self.NOT_FOUND_KEY, Versions.V2)):
            match_fhir_id_result = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)
            self.assertIsNone(match_fhir_id_result.fhir_id)
            self.assertIsNone(match_fhir_id_result.lookup_type)
            self.assertFalse(match_fhir_id_result.success)
            self.assertEqual(match_fhir_id_result.error, 'The requested Beneficiary has no entry, however this may change')
            self.assertEqual(match_fhir_id_result.error_type, MatchFhirIdErrorType.NOT_FOUND)

    def test_match_fhir_id_server_hicn_error(self):
        '''
            Testing responses: HICN = error
                               MBI = not_found
            Expecting: HTTPError exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.ERROR_KEY, self.NOT_FOUND_KEY, Versions.V2)):
            match_fhir_id_result = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)
            self.assertIsNone(match_fhir_id_result.fhir_id)
            self.assertIsNone(match_fhir_id_result.lookup_type)
            self.assertFalse(match_fhir_id_result.success)
            self.assertEqual(match_fhir_id_result.error_type, MatchFhirIdErrorType.UPSTREAM)

    def test_match_fhir_id_server_mbi_error(self):
        '''
            Testing responses: HICN = not_found
                               MBI = error
            Expecting: HTTPError exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.NOT_FOUND_KEY, self.ERROR_KEY, Versions.V2)):
            match_fhir_id_result = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)
            self.assertIsNone(match_fhir_id_result.fhir_id)
            self.assertIsNone(match_fhir_id_result.lookup_type)
            self.assertFalse(match_fhir_id_result.success)
            self.assertEqual(match_fhir_id_result.error_type, MatchFhirIdErrorType.UPSTREAM)

    def test_match_fhir_id_duplicates_hicn(self):
        '''
            Testing responses: HICN = duplicates
                               MBI = not_found
            Expecting: UpstreamServerException exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.NOT_FOUND_KEY, self.ERROR_KEY, Versions.V2)):
            match_fhir_id_result = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)
            self.assertIsNone(match_fhir_id_result.fhir_id)
            self.assertIsNone(match_fhir_id_result.lookup_type)
            self.assertFalse(match_fhir_id_result.success)
            self.assertIn('None for url', match_fhir_id_result.error)
            self.assertEqual(match_fhir_id_result.error_type, MatchFhirIdErrorType.UPSTREAM)

    def test_match_fhir_id_duplicates_mbi(self):
        '''
            Testing responses: HICN = success
                               MBI = duplicates
            Expecting: UpstreamServerException exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.SUCCESS_KEY, self.DUPLICATES_KEY, Versions.V2)):
            match_fhir_id_result = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)
            self.assertIsNone(match_fhir_id_result.fhir_id)
            self.assertIsNone(match_fhir_id_result.lookup_type)
            self.assertFalse(match_fhir_id_result.success)
            self.assertIn("Duplicate", match_fhir_id_result.error)
            self.assertEqual(match_fhir_id_result.error_type, MatchFhirIdErrorType.UPSTREAM)

    def test_match_fhir_id_duplicates_both(self):
        '''
            Testing responses: HICN = duplicates
                               MBI = duplicates
            Expecting: UpstreamServerException exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.DUPLICATES_KEY, self.DUPLICATES_KEY, Versions.V2)):
            match_fhir_id_result = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)
            self.assertIsNone(match_fhir_id_result.fhir_id)
            self.assertIsNone(match_fhir_id_result.lookup_type)
            self.assertFalse(match_fhir_id_result.success)
            self.assertIn("Duplicate", match_fhir_id_result.error)
            self.assertEqual(match_fhir_id_result.error_type, MatchFhirIdErrorType.UPSTREAM)

    def test_match_fhir_id_malformed_hicn(self):
        '''
            Testing responses: HICN = malformed
                               MBI = not_found
            Expecting: UpstreamServerException exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.MALFORMED_KEY, self.NOT_FOUND_KEY, Versions.V2)):
            match_fhir_id_result = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)
            self.assertIsNone(match_fhir_id_result.fhir_id)
            self.assertIsNone(match_fhir_id_result.lookup_type)
            self.assertFalse(match_fhir_id_result.success)
            self.assertIn('Unexpected in Patient search', match_fhir_id_result.error)
            self.assertEqual(match_fhir_id_result.error_type, MatchFhirIdErrorType.UPSTREAM)

    def test_match_fhir_id_malformed_mbi(self):
        '''
            Testing responses: HICN = success
                               MBI = malformed
            Expecting: UpstreamServerException exception raised
        '''
        with HTTMock(self.create_fhir_mock(self.SUCCESS_KEY, self.MALFORMED_KEY, Versions.V2)):
            match_fhir_id_result = match_fhir_id(
                mbi=self.test_mbi,
                hicn_hash=self.test_hicn_hash, request=self.request, version=Versions.V2)
            self.assertIsNone(match_fhir_id_result.fhir_id)
            self.assertIsNone(match_fhir_id_result.lookup_type)
            self.assertFalse(match_fhir_id_result.success)
            self.assertIn('Unexpected in Patient search', match_fhir_id_result.error)
            self.assertEqual(match_fhir_id_result.error_type, MatchFhirIdErrorType.UPSTREAM)
