from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import Group
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile, UserIdentificationLabel
from apps.fhir.bluebutton.models import Crosswalk
from waffle.testutils import override_switch


class CreateDeveloperAccountTestCase(TestCase):
    """
    Test Developer Account Creation
    """

    @override_switch('signup', active=True)
    def setUp(self):
        Group.objects.create(name='BlueButton')
        self.client = Client()
        self.url = reverse('accounts_create_account')
        # Create user self identification choices
        UserIdentificationLabel.objects.get_or_create(name="Self Identification #1",
                                                      slug="ident1",
                                                      weight=1)
        UserIdentificationLabel.objects.get_or_create(name="Self Identification #2",
                                                      slug="ident2",
                                                      weight=2)

    @override_switch('signup', active=True)
    @override_switch('login', active=True)
    def test_valid_account_create(self):
        """
        Create an Account Valid
        """
        ident_choice = UserIdentificationLabel.objects.get(slug="ident2")
        form_data = {
            'email': 'BamBam@Example.com',
            'organization_name': 'transhealth',
            'password1': 'bedrocks',
            'password2': 'bedrocks',
            'first_name': 'BamBam',
            'last_name': 'Rubble',
            'identification_choice': str(ident_choice.pk),
        }
        response = self.client.post(self.url, form_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please check your email')

        # verify username is lowercase
        User = get_user_model()
        u = User.objects.get(email="bambam@example.com")
        self.assertEqual(u.username, "bambam@example.com")
        self.assertEqual(u.email, "bambam@example.com")

        # Ensure developer account does not have a crosswalk entry.
        self.assertEqual(Crosswalk.objects.filter(user=u).exists(), False)

        # verify user has identification label chosen
        exist = User.objects.filter(useridentificationlabel__users=u).filter(useridentificationlabel__slug='ident2').exists()
        self.assertEqual(exist, True)

    @override_switch('signup', active=False)
    @override_switch('login', active=True)
    def test_valid_account_create_flag_off(self):
        """
        Create an Account Valid
        """
        ident_choice = UserIdentificationLabel.objects.get(slug="ident2")
        form_data = {
            'email': 'BamBam@Example.com',
            'organization_name': 'transhealth',
            'password1': 'bedrocks',
            'password2': 'bedrocks',
            'first_name': 'BamBam',
            'last_name': 'Rubble',
            'identification_choice': str(ident_choice.pk),
        }
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 404)

    @override_switch('signup', active=True)
    def test_account_create_shold_fail_when_password_too_short(self):
        """
        Create account should fail if password is too short
        """
        ident_choice = UserIdentificationLabel.objects.get(slug="ident2")
        form_data = {
            'invitation_code': '1234',
            'username': 'fred2',
            'organization_name': 'transhealth',
            'password1': 'p',
            'password2': 'p',
            'first_name': 'Fred',
            'last_name': 'Flinstone',
            'identification_choice': str(ident_choice.pk),
        }
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'too short')

    @override_switch('signup', active=True)
    def test_account_create_shold_fail_when_password_too_common(self):
        """
        Create account should fail if password is too common
        """
        ident_choice = UserIdentificationLabel.objects.get(slug="ident2")
        form_data = {
            'invitation_code': '1234',
            'username': 'fred',
            'organization_name': 'transhealth',
            'password1': 'password',
            'password2': 'password',
            'first_name': 'Fred',
            'last_name': 'Flinstone',
            'identification_choice': str(ident_choice.pk),
        }
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'too common')

    @override_switch('signup', active=True)
    def test_valid_account_create_is_a_developer(self):
        """
        Account Created on site is a developer and not a benny
        """
        ident_choice = UserIdentificationLabel.objects.get(slug="ident1")
        form_data = {
            'invitation_code': '1234',
            'email': 'hank@example.com',
            'organization_name': 'transhealth',
            'password1': 'bedrocks',
            'password2': 'bedrocks',
            'first_name': 'Hank',
            'last_name': 'Flinstone',
            'identification_choice': str(ident_choice.pk),
        }
        self.client.post(self.url, form_data, follow=True)
        up = UserProfile.objects.get(user__email='hank@example.com')
        self.assertEqual(up.user_type, 'DEV')
