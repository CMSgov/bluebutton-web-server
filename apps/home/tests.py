from __future__ import absolute_import
from __future__ import unicode_literals
from django.test.client import Client
from django.test import TestCase
from django.core.urlresolvers import reverse


__author__ = "Alan Viars"


class BlueButtonAPIMainPAgeTest(TestCase):
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
