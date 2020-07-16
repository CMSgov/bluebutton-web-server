import json
import logging
from io import StringIO
from datetime import datetime
from django.utils.dateparse import parse_duration
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from apps.fhir.bluebutton.models import Crosswalk
from apps.dot_ext.models import Approval, Application
from apps.test import BaseApiTest

from oauth2_provider.models import (
    get_access_token_model,
    get_refresh_token_model,
)

AccessToken = get_access_token_model()
RefreshToken = get_refresh_token_model()


class HTTPReqRespAuditLoggingTest(BaseApiTest):
    """
    Test audit loggers
    """
    def setUp(self):
        self.callback_url = reverse('mymedicare-sls-callback')
        self.login_url = reverse('mymedicare-login')
        Group.objects.create(name='BlueButton')

        self.http_reqresp_logger = logging.getLogger('audit.hhs_oauth_server.request_logging')
        self.http_reqresp_logger.setLevel(logging.INFO)
        self.http_reqresp_stream = StringIO()
        self.http_reqresp_ch = logging.StreamHandler(self.http_reqresp_stream)
        self.http_reqresp_ch.setLevel(logging.INFO)
        self.http_reqresp_logger.addHandler(self.http_reqresp_ch)
        for h in self.http_reqresp_logger.handlers:
            self.http_reqresp_logger.removeHandler(h)
        self.http_reqresp_logger.addHandler(self.http_reqresp_ch)

    def tearDown(self):
        # tear down http req resp audit logger
        self.http_reqresp_logger.removeHandler(self.http_reqresp_ch)
        del self.http_reqresp_logger, self.http_reqresp_ch, self.http_reqresp_stream

    def test_http_req_resp_audit_logging(self):
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
        log_entry = self.http_reqresp_stream.getvalue()
        log_lines = log_entry.splitlines()
        # {"start_time": 1594919285.813495, "end_time": 1594919285.822201, "request_uuid": "ea44a94c-c786-11ea-a01b-024
        # 2ac1b0004", "path": "/v1/o/authorize/d270a063-f30a-4c37-af52-ff4d35abbb9b/", "response_code": 302, "size": ""
        # , "location": "http://test.com?code=tRThAPj03WMPquNpvyujHpgeiygaOn", "app_name": "", "app_id": "", "dev_id":
        # "", "dev_name": "", "access_token_hash": "", "user": "bob", "ip_addr": "127.0.0.1"}
        for line in log_lines:
            json_rec = json.loads(line)
            self.assertTrue(json_rec["start_time"] is not None)
            self.assertTrue(json_rec["end_time"] is not None)
            self.assertTrue(json_rec["request_uuid"] is not None)
            self.assertTrue("path" in json_rec)
            self.assertTrue("location" in json_rec)
            self.assertTrue("app_name" in json_rec)
            self.assertTrue("app_id" in json_rec)
            self.assertTrue("dev_name" in json_rec)
            self.assertTrue("dev_id" in json_rec)
            self.assertTrue("user" in json_rec)
            self.assertTrue("access_token_hash" in json_rec)
            self.assertTrue("ip_addr" in json_rec)
