from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from django.urls import reverse
from apps.accounts.models import UserProfile


class LoginTestCase(TestCase):
    """
    Test standard user cannot reach admin login
    """

    def _create_user(self, username, password, **extra_fields):
        """
        Helper method that creates a user instance
        with `username` and `password` set.
        """
        user = User.objects.create_user(username,
                                        password=password,
                                        **extra_fields)
        return user

    def setUp(self):
        self._create_user('fred', 'bedrocks', first_name='Fred',
                          last_name='Flinstone', email='fred@example.com',
                          is_staff=False, is_active=True)
        user = User.objects.get(username='fred')
        UserProfile.objects.create(user=user)
        self.client = Client()
        self.client.login(username='fred', password='bedrocks')
        self.url = reverse('admin:login')

    def test_standard_user_cannot_reach_admin_login(self):
        """
        Test standard user cannot reach admin login
        """
        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        # Redirect to our MFA enabled login.
        self.assertNotContains(response, 'Administration')
        self.assertNotContains(response, 'admin/css/login', html=True)
