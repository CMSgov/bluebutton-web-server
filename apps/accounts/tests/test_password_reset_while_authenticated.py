from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.urls import reverse
from ..models import UserProfile


class ResetPasswordWhileAuthenticatedTestCase(TestCase):
    """
    Test Changing the password reset questions
    """

    def setUp(self):
        u = User.objects.create_user(username="fred",
                                     first_name="Fred",
                                     last_name="Flinstone",
                                     email='fred@example.com',
                                     password="foobarfoobarfoobar",)
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
        self.client.login(username="fred", password="foobarfoobarfoobar")
        url = reverse('reset_password')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_page_requires_authentication(self):
        url = reverse('reset_password')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_password_ischanged(self):
        self.client.login(username="fred", password="foobarfoobarfoobar")
        url = reverse('reset_password')
        form_data = {'password1': "ichangedthepassword",
                     "password2": "ichangedthepassword"}
        response = self.client.post(url, form_data, follow=True)
        self.assertContains(response, "Your password was updated.")
