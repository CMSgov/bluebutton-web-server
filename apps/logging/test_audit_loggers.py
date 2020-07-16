import json
import logging
import re
from io import StringIO
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from django.utils.dateparse import parse_duration
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from apps.fhir.bluebutton.models import Crosswalk
from apps.dot_ext.models import Approval, Application, ArchivedToken
from apps.test import BaseApiTest
from apps.authorization.models import DataAccessGrant, ArchivedDataAccessGrant

from oauth2_provider.models import (
    get_access_token_model,
    get_refresh_token_model,
)

AccessToken = get_access_token_model()
RefreshToken = get_refresh_token_model()


class SignalBasedAuditLoggingTest(BaseApiTest):
    """
    Test audit loggers
    """
    def setUp(self):
        self.callback_url = reverse('mymedicare-sls-callback')
        self.login_url = reverse('mymedicare-login')
        Group.objects.create(name='BlueButton')

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

    def test_appauthz_accesstoken_dataaccess_grantrevoke_logging(self):
        # Test that there are no errors with cascading deletes
        redirect_uri = 'http://localhost'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        self.client.login(username='anna', password='123456')
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(reverse('oauth2_provider:authorize'), data=payload)
        self.client.logout()
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret,
        }
        response = self.client.post('/v1/o/token/', data=token_request_data)
        self.assertEqual(response.status_code, 200)
        # Now we have a token and refresh token
        tkn = response.json()['access_token']
        refresh_tkn = response.json()['refresh_token']

        # Test for cascading contraint errors.
        application_pk = application.pk
        application.delete()
        # Test related objects are deleted
        self.assertFalse(AccessToken.objects.filter(token=tkn).exists())
        self.assertTrue(ArchivedToken.objects.filter(token=tkn).exists())
        self.assertFalse(RefreshToken.objects.filter(token=refresh_tkn).exists())
        self.assertFalse(DataAccessGrant.objects.filter(application__pk=application_pk).exists())
        self.assertTrue(ArchivedDataAccessGrant.objects.filter(application__pk=application_pk).exists())

        log_entries = self.token_stream.getvalue()
        log_lines = log_entries.splitlines()
        app_authorized_pattern = '.*type.*:.*Authorization.*user.*crosswalk.*'
        accesstoken_authorized_pattern = '.*type.*:.*AccessToken.*action.*authorized.*'
        accesstoken_revoked_pattern = '.*type.*:.*AccessToken.*action.*revoked.*'
        dataaccessgrant_revoked_pattern = '.*type.*:.*DataAccessGrant.*action.*revoked.*'
        has_app_authorized = False
        has_accesstoken_authorized = False
        has_accesstoken_revoked = False
        has_dataaccessgrant_revoked = False

        for line in log_lines:
            if re.match(app_authorized_pattern, line) is not None:
                has_app_authorized = True
            if re.match(accesstoken_authorized_pattern, line) is not None:
                has_accesstoken_authorized = True
            if re.match(accesstoken_revoked_pattern, line) is not None:
                has_accesstoken_revoked = True
            if re.match(dataaccessgrant_revoked_pattern, line) is not None:
                has_dataaccessgrant_revoked = True
        mesg_app_authz = 'Expect "type" : "Authorization" ... in log record, but not found.'
        mesg_token_authzd = 'Expect "type" : "AccessToken"..."action" : "revoked" ... in log record, but not found.'
        mesg_token_revoked = 'Expect "type" : "AccessToken"..."action" : "revoked" ... in log record, but not found.'
        mesg_data_grant_revoked = 'Expect "type" : "DataAccessGrant"..."action" : "revoked" ... in log record, but not found.'
        self.assertTrue(has_app_authorized, mesg_app_authz)
        self.assertTrue(has_accesstoken_authorized, mesg_token_authzd)
        self.assertTrue(has_accesstoken_revoked, mesg_token_revoked)
        self.assertTrue(has_dataaccessgrant_revoked, mesg_data_grant_revoked)

    def test_app_authorize_logging(self):
        user = User.objects.create_user(
            "bob",
            password="bad")
        Crosswalk.objects.create(
            user=user,
            fhir_id="-20000000002346",
            user_hicn_hash="96228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7")
        application = Application.objects.create(
            redirect_uris="http://test.com",
            authorization_grant_type='authorization-code',
            name="test01",
            user=user)

        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        application.scope.add(capability_a, capability_b)

        approval = Approval.objects.create(
            user=user)
        auth_uri = reverse(
            'oauth2_provider:authorize-instance',
            args=[approval.uuid])
        response = self.client.get(auth_uri, data={
            "client_id": application.client_id,
            "redirect_uri": "http://test.com",
            "response_type": "code"})
        self.assertEqual(200, response.status_code)
        approval.refresh_from_db()
        self.assertEqual(application, approval.application)
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(auth_uri, data={
            "client_id": "bad",
            "redirect_uri": "http://test.com",
            "response_type": "code"})
        self.assertEqual(302, response.status_code)

        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://test.com',
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(auth_uri, data=payload)
        self.assertEqual(302, response.status_code)
        self.assertIn("code=", response.url)
        approval.created_at = datetime.now() - parse_duration("601")
        approval.save()
        response = self.client.post(auth_uri, data={
            "client_id": application.client_id,
            "redirect_uri": "http://test.com",
            "response_type": "code"})
        # functional asserts
        self.assertEqual(302, response.status_code)
        log_entry = self.token_stream.getvalue()
        log_lines = log_entry.splitlines()
        like_a_app_authz = False
        # expect record like this:
        # {"type": "Authorization", "user": {"id": 1, "username": "bob", "crosswalk": {"id": 1, "user_hicn_
        # hash": "96228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7", "user_mbi_hash": null, "fhir_id":
        # "-20000000002346", "user_id_type": "H"}}, "application": {"id": 1, "name": "test01"}}
        for line in log_lines:
            try:
                json_rec = json.loads(line)
                if json_rec["type"] == "Authorization" and json_rec["user"] is not None \
                        and json_rec["application"] is not None:
                    like_a_app_authz = True
            except Exception:
                pass
        self.assertTrue(like_a_app_authz, "Expect Application Authorization event, Not found in [{}]".format(log_entry))
