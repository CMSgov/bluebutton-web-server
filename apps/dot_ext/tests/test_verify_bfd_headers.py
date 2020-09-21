from oauth2_provider.compat import parse_qs, urlparse
from oauth2_provider.models import AccessToken
from apps.test import BaseApiTest
from apps.authorization.models import DataAccessGrant
from ..models import Application
from apps.fhir.bluebutton.signals import pre_fetch
from apps.fhir.bluebutton.views.search import SearchView
from httmock import all_requests, HTTMock


class TestBFDHeaders(BaseApiTest):
    def fetching_data(self, sender, request=None, **kwargs):
        hdr = request.headers.get('includeAddressFields')
        self.assertTrue(hdr)
        self.assertEqual(hdr, "False")

    def setUp(self):
        pre_fetch.connect(self.fetching_data, sender=SearchView)

    def tearDown(self):
        pre_fetch.disconnect(self.fetching_data, sender=SearchView)

    def _create_test_token(self, user, application):
        # user logs in
        self.client.force_login(user)
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': application.redirect_uris,
            'scope': application.scopes().split(" "),
            'expires_in': 86400,
            'allow': True,
        }
        if application.authorization_grant_type == Application.GRANT_IMPLICIT:
            payload['response_type'] = 'token'
        response = self.client.post('/v1/o/authorize/', data=payload)
        self.client.logout()
        if response.status_code != 302:
            raise Exception(response.context_data)
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        if application.authorization_grant_type == Application.GRANT_IMPLICIT:
            fragment = parse_qs(urlparse(response['Location']).fragment)
            tkn = fragment.pop('access_token')[0]
        else:
            query_dict = parse_qs(urlparse(response['Location']).query)
            authorization_code = query_dict.pop('code')
            token_request_data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': application.redirect_uris,
                'client_id': application.client_id,
                'client_secret': application.client_secret,
            }

            response = self.client.post('/v1/o/token/', data=token_request_data)
            self.assertEqual(response.status_code, 200)
            # Now we have a token and refresh token
            tkn = response.json()['access_token']

        t = AccessToken.objects.get(token=tkn)
        return t

    def test_fhir_request_has_header(self):
        # create an app for a user and obtain a token
        anna = self._create_user('anna', '123456', fhir_id='19990000000002')
        capability_a = self._create_capability('token_management', [['DELETE', r'/v1/o/tokens/\d+/']], default=False)
        application = self._create_application(
            'an app', grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://example.it')
        application.scope.add(capability_a)
        tkn = self._create_test_token(anna, application)
        # check access token
        self.assertTrue(DataAccessGrant.objects.filter(
            beneficiary=anna,
            application=application,
        ).exists())

        @all_requests
        def catchall(url, req):
            return {
                'status_code': 200,
                'content':{"resourceType":"Patient","id":"-20140000008325","extension":[{"url":"https://bluebutton.cms.gov/resources/variables/race","valueCoding":{"system":"https://bluebutton.cms.gov/resources/variables/race","code":"1","display":"White"}}],"identifier":[{"system":"https://bluebutton.cms.gov/resources/variables/bene_id","value":"-20140000008325"},{"system":"https://bluebutton.cms.gov/resources/identifier/hicn-hash","value":"2025fbc612a884853f0c245e686780bf748e5652360ecd7430575491f4e018c5"}],"name":[{"use":"usual","family":"Doe","given":["Jane","X"]}],"gender":"unknown","birthDate":"2014-06-01","address":[{"district":"999","state":"15","postalCode":"99999"}]} # noqa
            }

        with HTTMock(catchall):
            self.client.get('/v1/fhir/Patient',
                            HTTP_AUTHORIZATION="Bearer " + tkn.token)
