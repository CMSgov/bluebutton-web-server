from django.test import TestCase
from rest_framework import exceptions
from requests.exceptions import HTTPError
from apps.fhir.bluebutton.exceptions import UpstreamServerException
from httmock import all_requests, HTTMock
from ..authentication import match_hicn_hash
from .responses import responses


class TestAuthentication(TestCase):

    def test_match_hicn_hash_success(self):
        @all_requests
        def fhir_mock(url, request):
            return responses['success']
        with HTTMock(fhir_mock):
            fhir_id, backend_data = match_hicn_hash("50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b")
            self.assertEqual(backend_data, responses['success']['content'])
            self.assertEqual(fhir_id, "-20000000002346")

    def test_match_hicn_hash_not_found(self):
        @all_requests
        def fhir_mock(url, request):
            return responses['not_found']
        with HTTMock(fhir_mock):
            with self.assertRaises(exceptions.NotFound):
                fhir_id, backend_data = match_hicn_hash("50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b")

    def test_match_hicn_hash_server_error(self):
        @all_requests
        def fhir_mock(url, request):
            return responses['error']
        with HTTMock(fhir_mock):
            with self.assertRaises(HTTPError):
                fhir_id, backend_data = match_hicn_hash("50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b")

    def test_match_hicn_hash_duplicates(self):
        @all_requests
        def fhir_mock(url, request):
            return responses['duplicates']
        with HTTMock(fhir_mock):
            with self.assertRaises(UpstreamServerException):
                fhir_id, backend_data = match_hicn_hash("50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b")

    def test_match_hicn_hash_malformed(self):
        @all_requests
        def fhir_mock(url, request):
            return responses['malformed']
        with HTTMock(fhir_mock):
            with self.assertRaises(KeyError):
                fhir_id, backend_data = match_hicn_hash("50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b")

    def test_match_hicn_hash_lying_duplicates(self):
        @all_requests
        def fhir_mock(url, request):
            return responses['lying']
        with HTTMock(fhir_mock):
            with self.assertRaises(UpstreamServerException):
                fhir_id, backend_data = match_hicn_hash("50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b")
