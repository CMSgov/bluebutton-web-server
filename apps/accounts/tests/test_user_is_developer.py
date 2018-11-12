from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import Group, User
from django.urls import reverse

from ..models import UserProfile


class DeveloperAccountTestCase(TestCase):
    """
    Test Developer Account Can Create Applications
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
        Group.objects.create(name='BlueButton')
        self.client = Client()
        self.url = reverse('home')

    def test_developer_can_register_apps(self):
        self.client.login(username="fred", password="foobar")
        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Logout')
        # Is the button on the main page? For now it is still on the top nav.
        # self.assertContains(
        #     response, 'btn-primary"> <i class="fa fa-key"></i>')
        self.assertContains(
            response, '<!-- test_developer_can_register_apps -->')
