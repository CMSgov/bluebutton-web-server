from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.test.client import Client
from django.urls import reverse
from apps.accounts.models import UserProfile


class LoginTestCase(TestCase):
    """
    Test Non-MFA login and logout
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
                          last_name='Flinstone', email='fred@example.com')
        user = User.objects.get(username='fred')
        UserProfile.objects.create(user=user)
        self.client = Client()
        self.url = reverse('mfa_login')
        Group.objects.create(name='BlueButton')

    def test_valid_login(self):
        """
        Valid User can login
        """
        form_data = {'username': 'fred', 'password': 'bedrocks'}
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Logout')

    def test_valid_login_case_insensitive_username(self):
        """
        Valid User can login and username is case insensitive
        """
        form_data = {'username': 'Fred', 'password': 'bedrocks'}
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Logout')

    def test_invalid_login(self):
        """
        Invalid user cannot login
        """
        form_data = {'username': 'fred', 'password': 'dino'}
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')

    def test_logout(self):
        """
        User can logout
        """
        self.client.login(username='fred', password='bedrocks')
        response = self.client.get(reverse('mylogout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')

    def test_valid_login_email(self):
        """
        Valid User can login using their email address
        """
        form_data = {'username': 'fred@example.com', 'password': 'bedrocks'}
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Logout')
