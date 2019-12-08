import unittest
import base64

from django.conf.urls import include, url
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import TestCase
from django.test.utils import override_settings

from oauth2_provider.models import get_application_model

from apps.dot_ext.authentication import SLSAuthentication


Application = get_application_model()
UserModel = get_user_model()


try:
    from rest_framework import permissions
    from rest_framework.views import APIView

    class MockView(APIView):
        permission_classes = (permissions.IsAuthenticated,)

        def get(self, request):
            return HttpResponse({"a": 1, "b": 2, "c": 3})

        def post(self, request):
            return HttpResponse({"a": 1, "b": 2, "c": 3})

    class SLSAuthView(MockView):
        authentication_classes = [SLSAuthentication]

    urlpatterns = [
        url(r"^oauth2/", include("oauth2_provider.urls")),
        url(r"^oauth2-test/$", SLSAuthView.as_view()),
    ]

    rest_framework_installed = True
except ImportError:
    rest_framework_installed = False


@override_settings(ROOT_URLCONF=__name__)
class TestOAuth2Authentication(TestCase):
    def setUp(self):

        self.test_username = "0123456789abcdefghijklmnopqrstuvwxyz"
        self.test_user = UserModel.objects.create_user("0123456789abcdefghijklmnopqrstuvwxyz", "test@example.com", "123456")
        self.dev_user = UserModel.objects.create_user("dev_user", "dev@example.com", "123456")

        self.application = Application.objects.create(
            name="Test Application",
            redirect_uris="http://localhost http://example.com http://example.org",
            user=self.dev_user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )

    def _create_authorization_header(self, client_id, client_secret):
        return "Basic {0}".format(base64.b64encode("{0}:{1}".format(client_id, client_secret).encode('utf-8')).decode('utf-8'))

    def _create_authentication_header(self, username):
        return "SLS {0}".format(base64.b64encode(username.encode('utf-8')).decode("utf-8"))

    @unittest.skipUnless(rest_framework_installed, "djangorestframework not installed")
    def test_authentication_allow(self):
        auth = self._create_authorization_header(self.application.client_id, self.application.client_secret)
        response = self.client.get("/oauth2-test/",
                                   HTTP_AUTHORIZATION=auth,
                                   HTTP_X_AUTHENTICATION=self._create_authentication_header(self.test_username))
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(rest_framework_installed, "djangorestframework not installed")
    def test_authentication_denied(self):
        auth = self._create_authorization_header(12345, "bogus")
        response = self.client.get("/oauth2-test/",
                                   HTTP_AUTHORIZATION=auth,
                                   HTTP_X_AUTHENTICATION=self._create_authentication_header(self.test_username))
        self.assertEqual(response.status_code, 403)

    def test_user_dne(self):
        auth = self._create_authorization_header(self.application.client_id, self.application.client_secret)
        response = self.client.get("/oauth2-test/",
                                   HTTP_AUTHORIZATION=auth,
                                   HTTP_X_AUTHENTICATION=self._create_authentication_header('bogus'))
        self.assertEqual(response.status_code, 404)

    def test_no_authentication(self):
        auth = self._create_authorization_header(self.application.client_id, self.application.client_secret)
        response = self.client.get("/oauth2-test/",
                                   HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 403)

    def test_bad_authentication(self):
        auth = self._create_authorization_header(self.application.client_id, self.application.client_secret)
        response = self.client.get("/oauth2-test/",
                                   HTTP_AUTHORIZATION=auth,
                                   HTTP_X_AUTHENTICATION="thisisabadheader")
        self.assertEqual(response.status_code, 404)

    def test_unknown_authentication(self):
        auth = self._create_authorization_header(self.application.client_id, self.application.client_secret)
        response = self.client.get("/oauth2-test/",
                                   HTTP_AUTHORIZATION=auth,
                                   HTTP_X_AUTHENTICATION="UUID thisisabadheader")
        self.assertEqual(response.status_code, 404)
