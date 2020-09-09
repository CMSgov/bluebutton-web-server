from django.urls import reverse
from django.test import TestCase
from apps.mymedicare_cb.views import generate_nonce
from apps.mymedicare_cb.models import AnonUserState
from httmock import urlmatch, all_requests, HTTMock
from django.contrib.auth.models import Group
from apps.fhir.bluebutton.signals import pre_fetch
from .responses import patient_response


class MyMedicareBlueButtonClientBFDRequest(TestCase):
    """
    Check BFD header includeAddressFields presents and has value False
    during the MyMedicare SLS Callback search beneficiary using mbi or hicn,
    adapted from test_callback.py test case, keep original asserts to mae sure
    good auth flow.
    """
    def fetching_data_test(self, sender, request=None, **kwargs):
        hdr = request.headers.get('includeAddressFields')
        self.assertTrue(hdr)
        self.assertEqual(hdr, "False")

    def setUp(self):
        pre_fetch.connect(self.fetching_data_test, dispatch_uid="1234567890-unique")
        self.callback_url = reverse('mymedicare-sls-callback')
        self.login_url = reverse('mymedicare-login')
        Group.objects.create(name='BlueButton')

    def tearDown(self):
        pre_fetch.disconnect(self.fetching_data_test, dispatch_uid="1234567890-unique")

    def test_sls_pt_search_has_header(self):
        # create a state
        state = generate_nonce()
        AnonUserState.objects.create(
            state=state,
            next_uri="http://www.google.com?client_id=test&redirect_uri=test.com&response_type=token&state=test")
        # mock sls token endpoint

        @urlmatch(netloc='dev.accounts.cms.gov', path='/v1/oauth/token')
        def sls_token_mock(url, request):
            return {
                'status_code': 200,
                'content': {'access_token': 'works'},
            }

        # mock sls user info endpoint
        @urlmatch(netloc='dev.accounts.cms.gov', path='/v1/oauth/userinfo')
        def sls_user_info_mock(url, request):
            return {
                'status_code': 200,
                'content': {
                    'sub': '00112233-4455-6677-8899-aabbccddeeff',
                    'given_name': '',
                    'family_name': '',
                    'email': 'bob@bobserver.bob',
                    'hicn': '1234567890A',
                    'mbi': '1SA0A00AA00',
                },
            }

        # mock fhir user info endpoint
        @urlmatch(netloc='fhir.backend.bluebutton.hhsdevcloud.us', path='/v1/fhir/Patient/')
        def fhir_patient_info_mock(url, request):
            return {
                'status_code': 200,
                'content': patient_response,
            }

        @all_requests
        def catchall(url, request):
            raise Exception(url)

        with HTTMock(sls_token_mock,
                     sls_user_info_mock,
                     fhir_patient_info_mock,
                     catchall):
            response = self.client.get(self.callback_url, data={'code': 'test', 'state': state})
            # assert http redirect
            self.assertEqual(response.status_code, 302)
            self.assertIn("client_id=test", response.url)
            self.assertIn("redirect_uri=test.com", response.url)
            self.assertNotIn('_auth_user_id', self.client.session)
