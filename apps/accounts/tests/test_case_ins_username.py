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
        u = User.objects.create_user(username="fred",
                                     first_name="Fred",
                                     last_name="Flinstone",
                                     email='fred@example.com',
                                     password="foobar",)
        UserProfile.objects.create(user=u,
                                   user_type="DEV",
                                   create_applications=True,
                                   password_reset_question_1='1',
                                   password_reset_answer_1='blue',
                                   password_reset_question_2='2',
                                   password_reset_answer_2='Frank',
                                   password_reset_question_3='3',
                                   password_reset_answer_3='Bentley')
        self.client = Client()

    def test_page_loads(self):
        self.client.login(username="fred", password="foobar")
        url = reverse('account_settings')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_all_fields_required(self):
        self.client.login(username="fred", password="foobar")
        url = reverse('account_settings')
        form_data = {'username': '',
                     'first_name': '',
                     'last_name': "",
                     'email': 'fred@example.com',
                     }
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')

    def test_username_forced_to_lower(self):
        self.client.login(username="fred", password="foobar")
        url = reverse('account_settings')
        form_data = {'username': 'FRED',
                     'first_name': 'Fred',
                     'last_name': "Flinstone",
                     'email': 'fred@example.com',
                     }
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'fred')
