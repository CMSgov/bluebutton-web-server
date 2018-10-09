from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import Group
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import Invitation, UserProfile
from apps.fhir.bluebutton.models import Crosswalk
from django.conf import settings


class CreateDeveloperAccountTestCase(TestCase):
    """
    Test Developer Account Creation
    """

    fixtures = ['testfixture']

    def setUp(self):
        Invitation.objects.create(code='1234', email='bambam@example.com')
        Group.objects.create(name='BlueButton')
        self.client = Client()
        self.url = reverse('accounts_create_account')

    def test_valid_account_create(self):
        """
        Create an Account Valid
        """
        form_data = {
            'invitation_code': '1234',
            'email': 'BamBam@Example.com',
            'organization_name': 'transhealth',
            'password1': 'bedrocks',
            'password2': 'bedrocks',
            'first_name': 'BamBam',
            'last_name': 'Rubble',
            'password_reset_question_1': '1',
            'password_reset_answer_1': 'blue',
            'password_reset_question_2': '2',
            'password_reset_answer_2': 'Jason',
            'password_reset_question_3': '3',
            'password_reset_answer_3': 'Jeep'
        }
        response = self.client.post(self.url, form_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please check your email')

        # verify username is lowercase
        User = get_user_model()
        u = User.objects.get(email="bambam@example.com")
        self.assertEqual(u.username, "bambam@example.com")
        self.assertEqual(u.email, "bambam@example.com")

        # Ensure developer account has a sample FHIR id crosswalk entry.
        self.assertEqual(Crosswalk.objects.filter(user=u,
                                                  fhir_id=settings.DEFAULT_SAMPLE_FHIR_ID).exists(), True)

    def test_account_create_shold_fail_when_password_too_short(self):
        """
        Create account should fail if password is too short
        """
        form_data = {
            'invitation_code': '1234',
            'username': 'fred2',
            'organization_name': 'transhealth',
            'password1': 'p',
            'password2': 'p',
            'first_name': 'Fred',
            'last_name': 'Flinstone',
            'password_reset_question_1': '1',
            'password_reset_answer_1': 'blue',
            'password_reset_question_2': '2',
            'password_reset_answer_2': 'Jason',
            'password_reset_question_3': '3',
            'password_reset_answer_3': 'Jeep'
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
            'username': 'fred',
            'organization_name': 'transhealth',
            'password1': 'password',
            'password2': 'password',
            'first_name': 'Fred',
            'last_name': 'Flinstone',
            'password_reset_question_1': '1',
            'password_reset_answer_1': 'blue',
            'password_reset_question_2': '2',
            'password_reset_answer_2': 'Jason',
            'password_reset_question_3': '3',
            'password_reset_answer_3': 'Jeep'
        }
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'too common')

    def test_valid_account_create_is_a_developer(self):
        """
        Account Created on site is a developer and not a benny
        """
        form_data = {
            'invitation_code': '1234',
            'email': 'hank@example.com',
            'organization_name': 'transhealth',
            'password1': 'bedrocks',
            'password2': 'bedrocks',
            'first_name': 'Hank',
            'last_name': 'Flinstone',
            'password_reset_question_1': '1',
            'password_reset_answer_1': 'blue',
            'password_reset_question_2': '2',
            'password_reset_answer_2': 'Jason',
            'password_reset_question_3': '3',
            'password_reset_answer_3': 'Jeep'
        }
        self.client.post(self.url, form_data, follow=True)
        up = UserProfile.objects.get(user__email='hank@example.com')
        self.assertEqual(up.user_type, 'DEV')
