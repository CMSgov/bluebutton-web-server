from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from ..models import UserProfile, ValidPasswordResetKey


class PasswordResetTestCase(TestCase):
    """
    Test Password Reset FunctionalityDeveloper Account Can Create Applications
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

    def test_password_reset_valid_user(self):
        url = reverse('forgot_password')
        form_data = {'email': 'fred'}
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Answer')

    def test_password_reset_invalid_user(self):
        url = reverse('forgot_password')
        form_data = {'email': 'derf'}
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'username supplied does not exist.')

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
