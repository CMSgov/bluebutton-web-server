from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.urls import reverse
from ..models import UserProfile
from waffle.testutils import override_switch


class PasswordResetTestCase(TestCase):

    """
    Test Password Reset FunctionalityDeveloper Account Can Create Applications
    """

    def setUp(self):

        u = User.objects.create_user(username="fred",
                                     first_name="Fred",
                                     last_name="Flinstone",
                                     email='fred@example.com',
                                     password="foobar",)
        UserProfile.objects.create(user=u,
                                   user_type="DEV",
                                   create_applications=True)
        self.client = Client()

    @override_switch('login', active=True)
    def test_password_reset_valid_user(self):
        url = reverse('forgot_password')
        form_data = {'email': 'fred@example.com'}
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)

    @override_switch('login', active=True)
    def test_password_reset_invalid_user(self):
        url = reverse('forgot_password')
        form_data = {'email': 'derf@example.com'}
        response = self.client.post(url, form_data, follow=True)
        self.assertRedirects(response, "/v1/accounts/password-reset-done", status_code=302, target_status_code=200,
                             msg_prefix='', fetch_redirect_response=True)
