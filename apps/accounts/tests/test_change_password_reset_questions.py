from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.urls import reverse

from ..models import UserProfile, ValidPasswordResetKey


class ChangePasswordResetQuestionsTestCase(TestCase):
    """
    Test Changing the password reset questions
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
        url = reverse('change_secret_questions')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_all_fields_required(self):
        self.client.login(username="fred", password="foobar")
        url = reverse('change_secret_questions')
        form_data = {'password_reset_question_1': '3',
                     'password_reset_answer_1': 'Ghostbusters',
                     'password_reset_question_2': '3',
                     'password_reset_answer_2': 'Fluffy',
                     'password_reset_question_3': '3',
                     'password_reset_answer_3': '',

                     }
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')

    def test_password_reset_invalid_user(self):
        url = reverse('forgot_password')
        form_data = {'email': 'derf@example.com'}
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with the email supplied does not exist.')

    def test_password_reset_invalid_answer_3(self):
        url = reverse('secret_question_challenge_3', args=('fred',))
        form_data = {'answer': 'Yogo'}
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wrong answer.')

    def test_password_reset_valid_answer_3(self):
        url = reverse('secret_question_challenge_3', args=('fred',))
        form_data = {'answer': 'bentley'}
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Please check your email for a special link to reset your password.')
        # Check that the password reset key was created.
        self.assertGreater(
            ValidPasswordResetKey.objects.filter(
                user__username='fred').count(), 0)
