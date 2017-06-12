from django.test import TestCase, override_settings
from django.contrib.auth.models import User, Group
from django.test.client import Client
from django.core.urlresolvers import reverse
from apps.accounts.models import UserProfile, MFACode
# from apps.accounts.views.core import pick_reverse_login


class MFALoginTestCase(TestCase):
    """
    Test MFA-login and logout
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

    @override_settings(LOGIN_RATE='5000/m')
    def setUp(self):
        self._create_user('fred', 'bedrocks', first_name='Fred',
                          last_name='Flinstone', email='fred@example.com')
        self.user = User.objects.get(username='fred')
        self.up = UserProfile.objects.create(user=self.user, mfa_login_mode="EMAIL",
                                             mobile_phone_number="555-555-5555")
        self.client = Client()
        self.url = reverse('mfa_login')
        Group.objects.create(name='BlueButton')

    @override_settings(LOGIN_RATE='5000/m')
    def test_valid_mfa_login_with_email(self):
        """
        Valid User can login with valid MFA code
        """
        form_data = {'username': 'fred', 'password': 'bedrocks'}
        response = self.client.post(self.url, form_data, follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(response.status_code, 200)
        # MFA user should not be logged in (yet)
        self.assertContains(response, 'Login')
        # Get the UID from the URL
        url_parts = last_url.split("/")
        uid = url_parts[-2]
        mfac = MFACode.objects.get(uid=uid)
        # complete the MFA process w/ valid code.
        response = self.client.post(
            reverse(
                'mfa_code_confirm', args=(
                    uid,)), {
                'code': mfac.code}, follow=True)
        # Now that a valid code is provided, the user is logged in (sees
        # Logout)
        self.assertContains(response, 'Logout')
        self.client.get(reverse('mylogout'))

    @override_settings(LOGIN_RATE='5000/m')
    def test_valid_mfa_login_with_sms(self):
        """
        Valid User can login with valid MFA code (SMS)
        """
        # Change the user p to use SMS
        self.up.mfa_login_mode = "SMS"
        self.up.save()
        form_data = {'username': 'fred', 'password': 'bedrocks'}
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(response.status_code, 200)
        # MFA user should not be logged in (yet)
        self.assertContains(response, 'Login')
        # Get the UID from the URL
        url_parts = last_url.split("/")
        uid = url_parts[-2]
        mfac = MFACode.objects.get(uid=uid)
        # complete the MFA process w/ valid code.
        response = self.client.post(
            reverse(
                'mfa_code_confirm', args=(
                    uid,)), {
                'code': mfac.code}, follow=True)
        # Now that a valid code is provided, the user is logged in (sees
        # Logout)
        self.assertContains(response, 'Logout')

    # @override_settings(MFACode=True)
    # def test_pick_reverse_login_mfa_true(self):
    #     """
    #
    #     :return:
    #     """
    #
    #     response = pick_reverse_login()
    #     self.assertContains(response, 'acounts/mfa/login')
    #
    # @override_settings(MFACode=False)
    # def test_pick_reverse_login_mfa_false(self):
    #     """
    #
    #     :return:
    #     """
    #
    #     response = pick_reverse_login()
    #     print("No:MFA_Login Response:%s" % response)
    #     self.assertContains(response, 'acounts/login')
