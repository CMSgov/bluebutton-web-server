import pytz

from datetime import datetime, timedelta
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import Group
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile, UserIdentificationLabel
from apps.fhir.bluebutton.models import Crosswalk
from waffle.testutils import override_switch
from ..models import ActivationKey

LOGIN_MSG_ACTIVATED = "Your account has been activated. You may now login"


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
            'password1': 'BEDrocks@123',
            'password2': 'BEDrocks@123',
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

    @override_switch('signup', active=True)
    @override_switch('login', active=True)
    def test_new_account_activation_key(self):
        """
        Create an Account Valid, and check:
        1. the activation key also created
        2. initial good account verify request return expected login page with expected message
        3. subsequent good account verify request return expected login page with expected message
        4. account verify url sent with fabricated key return message indicating there is an issue...
        """
        ident_choice = UserIdentificationLabel.objects.get(slug="ident2")
        form_data = {
            'email': 'TestActivation@Example.com',
            'organization_name': 'transhealth',
            'password1': 'BEDrocks@123',
            'password2': 'BEDrocks@123',
            'first_name': 'Activation001',
            'last_name': 'Activation',
            'identification_choice': str(ident_choice.pk),
        }

        response = self.client.post(self.url, form_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please check your email')

        # verify username is lowercase
        User = get_user_model()
        u = User.objects.get(email="testactivation@example.com")
        self.assertEqual(u.username, "testactivation@example.com")
        self.assertEqual(u.email, "testactivation@example.com")
        self.assertFalse(u.is_active)

        # Ensure developer account does not have a crosswalk entry.
        self.assertEqual(Crosswalk.objects.filter(user=u).exists(), False)
        key = ActivationKey.objects.get(user=u.id)
        self.assertEqual(key.key_status, "created")
        self.assertIsNotNone(key.created_at)
        self.assertIsNone(key.expired_at)
        self.assertIsNone(key.activated_at)

        # simulate account verify link clicked, and account activated
        response = self.client.get(reverse('activation_verify', args=(key.key,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(LOGIN_MSG_ACTIVATED, response.content.decode('utf-8'))

        # simulate account verify link clicked again (it's OK), and should say: account activated
        response = self.client.get(reverse('activation_verify', args=(key.key,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(LOGIN_MSG_ACTIVATED, response.content.decode('utf-8'))

        # simulate account verify link played with a fabricated key, indicate issue and show contact
        response = self.client.get(reverse('activation_verify', args=(key.key + "x",)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("There may be an issue with your account.", response.content.decode('utf-8'))
        self.assertIn("Contact us at bluebuttonapi@cms.hhs.gov", response.content.decode('utf-8'))

    @override_switch('signup', active=True)
    @override_switch('login', active=True)
    def test_new_account_activation_key_expired(self):
        """
        Create an Account Valid, and check:
        account verify request sent after the activation key expired, should be redirected to login page
        with message indicating so
        """
        ident_choice = UserIdentificationLabel.objects.get(slug="ident2")
        form_data = {
            'email': 'TestActivation02@Example.com',
            'organization_name': 'transhealth',
            'password1': 'BEDrocks@123',
            'password2': 'BEDrocks@123',
            'first_name': 'Activation002',
            'last_name': 'Activation002',
            'identification_choice': str(ident_choice.pk),
        }

        response = self.client.post(self.url, form_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please check your email')

        # verify username is lowercase
        User = get_user_model()
        u = User.objects.get(email="testactivation02@example.com")
        self.assertEqual(u.username, "testactivation02@example.com")
        self.assertEqual(u.email, "testactivation02@example.com")
        self.assertFalse(u.is_active)

        # Ensure developer account does not have a crosswalk entry.
        self.assertEqual(Crosswalk.objects.filter(user=u).exists(), False)
        key = ActivationKey.objects.get(user=u.id)
        # Initial key has expected attributes values
        self.assertEqual(key.key_status, "created")
        self.assertIsNotNone(key.created_at)
        self.assertIsNone(key.expired_at)
        self.assertIsNone(key.activated_at)

        # simulate account activation key expired
        now = pytz.utc.localize(datetime.utcnow())
        expires = now - timedelta(hours=1)
        key.save(expires=expires)
        key = ActivationKey.objects.get(user=u.id)

        # simulate account verify link played with a fabricated key, indicate issue and show contact
        response = self.client.get(reverse('activation_verify', args=(key.key,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("The activation key is expired.", response.content.decode('utf-8'))
        self.assertIn("Contact us at bluebuttonapi@cms.hhs.gov for further assistance", response.content.decode('utf-8'))

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
            'password1': 'BEDrocks@123',
            'password2': 'BEDrocks@123',
            'first_name': 'BamBam',
            'last_name': 'Rubble',
            'identification_choice': str(ident_choice.pk),
        }
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 404)

    @override_switch('signup', active=True)
    def test_account_create_should_fail_when_password_too_short(self):
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
    def test_account_create_should_fail_when_password_too_common(self):
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
            'password1': 'BEDrocks@123',
            'password2': 'BEDrocks@123',
            'first_name': 'Hank',
            'last_name': 'Flinstone',
            'identification_choice': str(ident_choice.pk),
        }
        self.client.post(self.url, form_data, follow=True)
        up = UserProfile.objects.get(user__email='hank@example.com')
        self.assertEqual(up.user_type, 'DEV')
