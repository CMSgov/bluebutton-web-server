import json

from django.test.client import Client
from httmock import HTTMock, all_requests
from apps.test import BaseApiTest


class TestHealthchecks(BaseApiTest):

    def setUp(self):
        self.client = Client()
        self.url = "http://localhost"

    @all_requests
    def catchall(url, req, params):
        return {
            'status_code': 200,
            'content': '{"test": 1}',  # bfd check looks for json for success
        }

    def test_health_external(self):
        with HTTMock(self.catchall):
            self._call_health_external_endpoint(False)

    def test_health_external_endpoint_v2(self):
        with HTTMock(self.catchall):
            self._call_health_external_endpoint(True)

    def _call_health_external_endpoint(self, v2=False):
        with HTTMock(self.catchall):
            response = self.client.get(self.url + "/health/external_v2" if v2 else "/health/external")
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        msg = None
        try:
            msg = content['message']
        except KeyError:
            pass
        self.assertEqual(msg, "all's well")

    def test_health_bfd_endpoint(self):
        self._call_health_bfd_endpoint(False)

    def test_health_bfd_endpoint_v2(self):
        self._call_health_bfd_endpoint(True)

    def _call_health_bfd_endpoint(self, v2=False):
        with HTTMock(self.catchall):
            response = self.client.get(self.url + "/health/bfd_v2" if v2 else "/health/bfd")
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        msg = None
        try:
            msg = content['message']
        except KeyError:
            pass
        self.assertEqual(msg, "all's well")

    def test_health_db_endpoint(self):
        response = self.client.get(self.url + "/health/db")
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        msg = None
        try:
            msg = content['message']
        except KeyError:
            pass
        self.assertEqual(msg, "all's well")

    def test_health_sls_endpoint(self):
        with HTTMock(self.catchall):
            response = self.client.get(self.url + "/health/sls")
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        msg = None
        try:
            msg = content['message']
        except KeyError:
            pass
        self.assertEqual(msg, "all's well")
