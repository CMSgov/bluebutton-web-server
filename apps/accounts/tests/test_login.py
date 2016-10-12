from django.test import TestCase

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.test.client import Client
from django.core.urlresolvers import reverse
from apps.accounts.models import UserProfile
from getenv import env
from unittest import skipUnless


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

    def test_settings_auth_results_in_usertype_benny(self):
        """
        When user is authenticated by external source then presumed a benny
        password =
        pbkdf2_sha256$24000$V6XjGqYYNGY7$13tFC13aa
        TohxBgP2W3glTBz6PSbQN4l6HmUtxQrUys=

        set with
        export DJANGO_SLS_PASSWORD='pbkdf2_sha256$24000$V6XjGqYYNGY7$13tFC13aa
        TohxBgP2W3glTBz6PSbQN4l6HmUtxQrUys='
        """
        form_data = {'username': 'ben',
                     'password': 'bluebutton'}
        response = self.client.post(self.url,
                                    form_data,
                                    follow=True)

        if 'apps.accounts.auth.SettingsBackend' in settings.AUTHENTICATION_BACKENDS:

            up = UserProfile.objects.get(user__username='ben')
            # User is a beneficiary ()
            self.assertEqual(up.user_type, 'BEN')
            # User is not yet active. Pending activation.
            self.assertContains(response, 'Please check your email')
            self.assertEqual(up.user.is_active, False)

        else:
            # No SLS Auth in backend
            SLS_Auth_disabled = True
            self.assertEqual(SLS_Auth_disabled, True)

    @skipUnless(env('MM_USER', ''),
                "Requires real MyMedicare credentials. Test locally")
    def test_mymedicare_valid_login_succeeds(self):
        """
        Test MyMedicare valid login succeeds.
        When user is authenticated by MyMedicare, then user is presumed a benny
        """
        form_data = {'username': env('MM_USER', 'CHANGE_ME'),
                     'password': env('MM_PASS', 'CHANGE_ME')}
        response = self.client.post(self.url,
                                    form_data,
                                    follow=True)
        up = UserProfile.objects.get(
            user__username=env(
                'MM_USER', 'CHANGE_ME'))
        # This user is a beneficiary.
        self.assertEqual(up.user_type, 'BEN')
        # The user is logged in
        self.assertContains(response, "Logout")
