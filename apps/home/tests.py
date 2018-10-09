from django.test.client import Client
from django.test import TestCase
from django.urls import reverse


class BlueButtonAPIMainPageTest(TestCase):
    """
    Test that the main page returns 200
    """

    def setUp(self):
        self.client = Client()

    def test_main_page_200(self):
        """
        Test main page / returns 200.
        """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
