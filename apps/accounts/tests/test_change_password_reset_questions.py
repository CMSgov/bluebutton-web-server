from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.urls import reverse
from waffle.testutils import override_switch
from ..models import UserProfile


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
                                   create_applications=True)
        self.client = Client()

    @override_switch('login', active=True)
    def test_password_reset_invalid_user(self):
        url = reverse('forgot_password')
        form_data = {'email': 'derf@example.com'}
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
