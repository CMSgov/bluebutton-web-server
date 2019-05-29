from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.urls import reverse
from ..models import UserProfile


class CheckCaseInsensitiveUsernameTestCase(TestCase):
    """
    Test  username is always forces to lowercase.
    """

    def setUp(self):
        u = User.objects.create_user(username="fred@example.com",
                                     first_name="Fred",
                                     last_name="Flinstone",
                                     email='fred@example.com',
                                     password="foobar",)
        UserProfile.objects.create(user=u,
                                   user_type="DEV",
                                   create_applications=True)
        self.client = Client()

    def test_page_loads(self):
        self.client.login(username="fred@example.com", password="foobar")
        url = reverse('account_settings')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_all_fields_required(self):
        self.client.login(username="fred@example.com", password="foobar")
        url = reverse('account_settings')
        form_data = {'username': '',
                     'email': 'fred@example.com',
                     'first_name': '',
                     'last_name': "",
                     'organization_name': "Flinstone INC.",
                     }
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')

    def test_username_forced_to_lower(self):
        self.client.login(username="fred@example.com", password="foobar")
        url = reverse('account_settings')
        form_data = {'username': 'FRED@Example.com',
                     'email': 'fred@example.com',
                     'first_name': 'Fred',
                     'last_name': "Flinstone",
                     'organization_name': "Flinstone INC.",
                     }
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'fred@example.com')
