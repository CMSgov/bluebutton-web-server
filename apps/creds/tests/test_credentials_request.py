from django.test.client import Client
from ..models import CredentialingReqest
from django.urls import reverse
from apps.test import BaseApiTest
import datetime
from rest_framework import exceptions
from apps.dot_ext.models import Application
import json


class CredentialsTestCase(BaseApiTest):
    def setUp(self):
        # Test App #1: happy path
        dev_user1 = self._create_user("developer_test", "123456")
        test_app1 = self._create_application(
            "test_app_1", user=dev_user1, data_access_type="THIRTEEN_MONTH"
        )
        CredentialingReqest.objects.create(
            application=test_app1)

        # Test App #2: expired credentials
        dev_user2 = self._create_user("developer_test_2", "789123")
        test_app2 = self._create_application(
            "test_app_2", user=dev_user2, data_access_type="THIRTEEN_MONTH"
        )
        CredentialingReqest.objects.create(
            application=test_app2)

        # Test App #3: credentials retrieved before, re-download/re-fetched not allowed
        dev_user3 = self._create_user("developer_test_3", "123456")
        test_app3 = self._create_application(
            "test_app_3", user=dev_user3, data_access_type="THIRTEEN_MONTH"
        )
        CredentialingReqest.objects.create(
            application=test_app3)
        created_date = datetime.date(2018, 1, 1)
        CredentialingReqest.objects.filter(application=Application.objects.get(name='test_app_3')).update(updated_at=created_date)
        CredentialingReqest.objects.filter(application=Application.objects.get(name='test_app_3')).update(visits_count=1)

        self.client = Client()

    def test_fetch_credentials(self):
        """
        Tests that GET requests to /creds/{{creds_req_id}}/?action=fetch endpoint
        retrieves and shows secret results, updates visit count, has a UUID with the correct length,
        the right template was used to render the response, and verified template content
        """
        creds_req_id = CredentialingReqest.objects.get(application=Application.objects.get(name='test_app_1')).id
        url = reverse('credentials_request', kwargs={'prod_cred_req_id': creds_req_id})
        response = self.client.get(url, {"action": "fetch"}, follow=True)
        self.assertEqual(len(str(creds_req_id)), 36)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'get_creds.html')
        self.assertContains(response, 'Application: ' + 'test_app_1')
        self.assertContains(response, 'App Credentials')
        self.assertEqual(response.context['fetch'], 'fetch')
        self.assertIsNotNone(response.context['client_id'])
        self.assertIsNotNone(response.context['client_secret_plain'])
        self.assertEqual(len(str(response.context['client_secret_plain'])), 128)
        updated_cred_req = CredentialingReqest.objects.get(pk=creds_req_id)
        self.assertEqual(updated_cred_req.visits_count, 1)

    def test_download_credentials(self):
        """
        Tests that GET requests to /creds/{{creds_req_id}}/?action=download endpoint
        retrieves secret results and downloaded JSON, updates visit count, and has a UUID with the correct length
        """
        creds_req_id = CredentialingReqest.objects.get(application=Application.objects.get(name='test_app_1')).id
        url = reverse('credentials_request', kwargs={'prod_cred_req_id': creds_req_id})
        response = self.client.get(url, {"action": "download"}, follow=True)
        self.assertEqual(len(str(creds_req_id)), 36)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="{}.json"'.format(creds_req_id))
        self.assertContains(response, 'client_id')
        self.assertContains(response, 'client_secret_plain')
        json_response = json.loads(response.content)
        self.assertEqual(len(str(json_response['client_secret_plain'])), 128)
        updated_cred_req = CredentialingReqest.objects.get(pk=creds_req_id)
        self.assertEqual(updated_cred_req.visits_count, 1)

    def test_fail_to_download_credentials(self):
        """
        Tests that GET requests to /creds/{{creds_req_id}}/?action=download endpoint in which credentials have already
        been fetched/downloaded do not permit a re-fetch/re-download, visit count does not get updated,
        and has a UUID with the correct length
        """
        creds_req_id = CredentialingReqest.objects.get(application=Application.objects.get(name='test_app_3')).id
        url = reverse('credentials_request', kwargs={'prod_cred_req_id': creds_req_id})
        response = self.client.get(url, {"action": "download"}, follow=True)
        self.assertEqual(len(str(creds_req_id)), 36)
        self.assertEqual(response.status_code, 403)
        self.assertRaisesRegex(exceptions.PermissionDenied, 'Credentials already fetched (download), doing it again not allowed.')
        updated_cred_req = CredentialingReqest.objects.get(pk=creds_req_id)
        self.assertEqual(updated_cred_req.visits_count, 1)

    def test_expired_credentials(self):
        """
        Tests that generated credentialing request expire and has a UUID with the correct length
        """
        creds_req_id = CredentialingReqest.objects.get(application=Application.objects.get(name='test_app_2')).id
        (CredentialingReqest.objects.filter(application=Application.objects.get(name='test_app_2'))
         .update(created_at=datetime.date(2018, 1, 1)))
        url = reverse('credentials_request', kwargs={'prod_cred_req_id': creds_req_id})
        response = self.client.get(url, {"action": "fetch"}, follow=True)
        self.assertEqual(len(str(creds_req_id)), 36)
        self.assertEqual(response.status_code, 403)
        self.assertRaisesRegex(exceptions.PermissionDenied, 'Generated credentialing request expired.')

    def test_credential_request_missing(self):
        """
        Tests when a credentialing request is not found and should throw the correct exception
        """
        creds_req_id = '7e909cd4-e9e7-47a3-bb6e-6837a23038c3'
        url = reverse('credentials_request', kwargs={'prod_cred_req_id': creds_req_id})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertRaisesRegex(exceptions.NotFound, 'Credentialing request not found.')
