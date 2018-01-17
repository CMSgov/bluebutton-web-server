from django.test import TestCase
from django.core.urlresolvers import reverse
from .models import AnonUserState

__author__ = "Alan Viars"


class MyMedicareBlueButtonClientApiUserInfoTest(TestCase):
    """
    Tests for the MyMedicare login and SLS Callback
    """

    def setUp(self):
        self.callback_url = reverse('mymedicare-sls-callback')
        # note this login requires next value.
        self.login_url = "%s?next=/" % (reverse('mymedicare-login'))

    def test_login_url_happy(self):
        """
        Test well-formed login_url has expected content
        """
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 302)

    def test_callback_url(self):
        """
        Test callback_url raises an error when
        necessary GET parameter state is missing.
        """
        with self.assertRaises(AnonUserState.DoesNotExist):
            self.client.get(self.callback_url)
