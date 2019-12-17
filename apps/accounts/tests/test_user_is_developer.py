from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import Group, User
from django.urls import reverse

from ..models import UserProfile

# TODO this should test that bennie accounts cannot create applications
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
        # TODO why is there a 'create_applications' flag as well as a DEV flag?
        # If logic around the create_applications flag is what's been tested,
        # there should be a test for DEV accounts that have this flag set to false
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
