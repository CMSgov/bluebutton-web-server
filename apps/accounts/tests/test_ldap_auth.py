from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import Group
from django.test.client import Client
from django.core.urlresolvers import reverse
from apps.accounts.models import UserProfile
# from ..ldap_auth import LDAPBackend
from unittest import skipUnless


__author__ = "Alan Viars"


class LDAPLoginTestCase(TestCase):
    """
    Test LDAP Login if the LDAP module is installed.
    """

    def setUp(self):
        self.client = Client()
        self.url = reverse('mfa_login')
        Group.objects.create(name='BlueButton')

    @skipUnless('django_ldap.backends.ldap_auth.LDAPBackend' in settings.AUTHENTICATION_BACKENDS,
                "Skip unless LDAP auth backend is active.")
    def test_mymedicare_valid_login_succeeds(self):
        """
        Test LDAP valid login succeeds.

        Ensure ldap server has user with uid=acv and password=secret
        When user is authenticated, then user is presumed a benny
        """
        username = "acv"
        password = "secret"

        with self.settings(AUTHENTICATION_BACKENDS=('apps.accounts.ldap_auth.LDAPBackend',)):

            form_data = {'username': username,
                         'password': password}
            response = self.client.post(self.url,
                                        form_data,
                                        follow=True)
            # The user is logged in
            self.assertContains(response, "Logout")

            up = UserProfile.objects.get(user__username=username)
            # This user is a beneficiary.
            self.assertEqual(up.user_type, 'BEN')
            # The user is logged in
            self.assertContains(response, "Logout")

    @skipUnless('django_ldap.backends.ldap_auth.LDAPBackend' in settings.AUTHENTICATION_BACKENDS,
                "Skip unless LDAP auth backend is active.")
    def test_mymedicare_invalid_login_fails(self):
        """
        Test LDAP invalid login attempt fails.

        """
        username = "acv"
        password = "i-dont-know-the-secret"

        with self.settings(AUTHENTICATION_BACKENDS=('apps.accounts.ldap_auth.LDAPBackend',)):

            form_data = {'username': username,
                         'password': password}
            response = self.client.post(self.url,
                                        form_data,
                                        follow=True)
            # The user is logged in
            self.assertContains(response, "Login")
