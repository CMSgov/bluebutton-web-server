from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from ..models import UserProfile, UserRegisterCode


class RegisterEndUserTestCase(TestCase):
    """
    Test End user account creationAccount Creation
    """

    def setUp(self):
        UserRegisterCode.objects.create(code='1234', email='fred@example.com')
        Group.objects.create(name='BlueButton')
        self.client = Client()
        self.url = reverse('create_end_user_account')

    def test_valid_account_create(self):
        """
        Create an Account Valid
        """
        form_data = {
            'invitation_code': '1234',
            'id_number': '123456789',
            'email': 'BARNEY@Example.com',
            'username': 'Barney',
            'password1': 'bedrocks',
            'password2': 'bedrocks',
            'first_name': 'Barney',
            'last_name': 'Rubble',
            'this_is_me_or_agent': True,
            'agree_to_terms': True,
            'human': '5'
        }
        response = self.client.get(self.url)
        form_data['human'] = response.content.partition("the answer is ".encode())[
            2].split('.'.encode(), 1)[0].decode()
        response = self.client.post(self.url, form_data, follow=True)

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'check your email')

        # verify username is lowercase
        User = get_user_model()
        u = User.objects.get(username="barney")
        self.assertEqual(u.username, "barney")
        self.assertEqual(u.email, "barney@example.com")
        # Verify the user is a beneficiary
        up = UserProfile.objects.get(user__username='barney')
        self.assertEqual(up.user_type, 'BEN')

    def test_account_create_shold_fail_when_password_too_short(self):
        """
        Create account should fail if password is too short
        """
        form_data = {
            'invitation_code': '1234',
            'id_number': '123456789',
            'email': 'BARNEY2@Example.com',
            'username': 'Barney2',
            'password1': 'short',
            'password2': 'short',
            'this_is_me_or_agent': True,
            'agree_to_terms': True,
            'first_name': 'Barney',
            'last_name': 'Rubble',
        }
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'too short')

    def test_account_create_shold_fail_when_password_too_common(self):
        """
        Create account should fail if password is too common
        """
        form_data = {
            'invitation_code': '1234',
            'id_number': '123456789',
            'email': 'BARNEY3@Example.com',
            'username': 'Barney3',
            'password1': 'password ',
            'password2': 'password',
            'first_name': 'Barney',
            'last_name': 'Rubble',
            'this_is_me_or_agent': True,
            'agree_to_terms': True,
        }
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'too common')
