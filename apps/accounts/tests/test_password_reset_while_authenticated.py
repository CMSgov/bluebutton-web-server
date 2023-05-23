import time
from datetime import datetime
import pytz
from dateutil.relativedelta import relativedelta
from unittest import mock
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from waffle.testutils import override_switch

from ..models import UserProfile
from ..validators import PasswordReuseAndMinAgeValidator


class StubDate(datetime):
    pass


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

        u_staff = User.objects.create_user(username="staff",
                                           first_name="staff",
                                           last_name="staff",
                                           email='staff@example.com',
                                           password="foobarfoobarfoobar",)
        UserProfile.objects.create(user=u_staff,
                                   user_type="DEV",
                                   create_applications=True,
                                   password_reset_question_1='1',
                                   password_reset_answer_1='blue',
                                   password_reset_question_2='2',
                                   password_reset_answer_2='Frank',
                                   password_reset_question_3='3',
                                   password_reset_answer_3='Bentley')
        u_staff.is_staff = True
        u_staff.save()
        self.client = Client()

    @override_switch('login', active=True)
    def test_page_loads(self):
        request = HttpRequest()
        self.client.login(request=request, username="fred", password="foobarfoobarfoobar")
        url = reverse('password_change')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    @override_switch('login', active=True)
    def test_page_requires_authentication(self):
        url = reverse('password_change')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    @override_switch('login', active=True)
    @mock.patch("apps.accounts.validators.datetime", StubDate)
    def test_password_ischanged(self):
        request = HttpRequest()
        self.client.login(request=request, username="fred", password="foobarfoobarfoobar")
        url = reverse('password_change')
        form_data = {'old_password': 'foobarfoobarfoobar',
                     'new_password1': 'IchangedTHEpassword#123',
                     'new_password2': 'IchangedTHEpassword#123'}
        self.user = User.objects.get(username="fred")
        # add 2 minutes to time to let min password age elapse
        StubDate.now = classmethod(
            lambda cls, timezone: datetime.now().replace(tzinfo=pytz.UTC)
                                  + relativedelta(minutes=+2)
        )
        response = self.client.post(url, form_data, follow=True)
        self.assertContains(response, "Your password was updated.")
        self.user = User.objects.get(username="fred")  # get user again so that you can see updated password
        self.assertEquals(self.user.check_password("IchangedTHEpassword#123"), True)

    @override_switch('login', active=True)
    @mock.patch("apps.accounts.validators.datetime", StubDate)
    def test_password_change_complexity_and_min_age_validation(self):
        request = HttpRequest()
        self.client.login(request=request, username="fred", password="foobarfoobarfoobar")
        url = reverse('password_change')
        # add 2 minutes to time to let min password age elapse
        StubDate.now = classmethod(
            lambda cls, timezone: datetime.now().replace(tzinfo=pytz.UTC)
                                  + relativedelta(minutes=+2)
        )
        form_data = {'old_password': 'foobarfoobarfoobar',
                     'new_password1': 'Ichangedthepassword#123',
                     'new_password2': 'Ichangedthepassword#123'}
        response = self.client.post(url, form_data, follow=True)
        self.assertContains(response, "Password must contain at least 2 upper case letter(s)")
        self.user = User.objects.get(username="fred")  # get user again so that you can see password not updated
        self.assertEquals(self.user.check_password("foobarfoobarfoobar"), True)
        form_data = {'old_password': 'foobarfoobarfoobar',
                     'new_password1': 'IchangedthePassword123',
                     'new_password2': 'IchangedthePassword123'}
        response = self.client.post(url, form_data, follow=True)
        self.assertContains(response, "Password must contain at least 1 special character(s)")
        self.user = User.objects.get(username="fred")  # get user again so that you can see password not updated
        self.assertEquals(self.user.check_password("foobarfoobarfoobar"), True)
        form_data = {'old_password': 'foobarfoobarfoobar',
                     'new_password1': 'IchangedthePassword@123',
                     'new_password2': 'IchangedthePassword@123'}
        response = self.client.post(url, form_data, follow=True)
        self.assertContains(response, "Your password was updated.")
        self.user = User.objects.get(username="fred")  # get user again so that you can see password has been updated
        self.assertEquals(self.user.check_password("IchangedthePassword@123"), True)
        form_data = {'old_password': 'IchangedthePassword@123',
                     'new_password1': 'ChangeP@ssw0rd2S00n',
                     'new_password2': 'ChangeP@ssw0rd2S00n'}
        # let time come back as current so no time will have passed
        StubDate.now = classmethod(
            lambda cls, timezone: datetime.now().replace(tzinfo=pytz.UTC)
        )
        response = self.client.post(url, form_data, follow=True)
        self.assertContains(response, "You can not change password that does not satisfy minimum password age")
        self.user = User.objects.get(username="fred")  # get user again so that you can see password not updated
        self.assertEquals(self.user.check_password("IchangedthePassword@123"), True)

    @override_switch('login', active=True)
    @mock.patch("apps.accounts.validators.datetime", StubDate)
    def test_password_change_reuse_validation(self):
        request = HttpRequest()
        self.client.login(request=request, username="fred", password="foobarfoobarfoobar")
        url = reverse('password_change')

        # first password change
        form_data = {'old_password': 'foobarfoobarfoobar',
                     'new_password1': 'IchangedTHEpassword#123',
                     'new_password2': 'IchangedTHEpassword#123'}
        # add 2 minutes to time to let min password age elapse
        StubDate.now = classmethod(
            lambda cls, timezone: datetime.now().replace(tzinfo=pytz.UTC)
                        + relativedelta(minutes=+2)
        )
        response = self.client.post(url, form_data, follow=True)
        self.assertContains(response, "Your password was updated.")
        self.user = User.objects.get(username="fred")  # get user again so that you can see password changed
        self.assertEquals(self.user.check_password("IchangedTHEpassword#123"), True)

        # 2nd password change
        form_data = {'old_password': 'IchangedTHEpassword#123',
                     'new_password1': '2ndChange#Pass',
                     'new_password2': '2ndChange#Pass'}
        # add 2 minutes to time to let min password age elapse
        StubDate.now = classmethod(
            lambda cls, timezone: datetime.now().replace(tzinfo=pytz.UTC)
                                  + relativedelta(minutes=+2)
        )
        response = self.client.post(url, form_data, follow=True)
        self.assertContains(response, "Your password was updated.")
        self.user = User.objects.get(username="fred")  # get user again so that you can see password changed
        self.assertEquals(self.user.check_password("2ndChange#Pass"), True)

        # 3rd password change - re-use password used in 1st
        form_data = {'old_password': '2ndChange#Pass',
                     'new_password1': 'IchangedTHEpassword#123',
                     'new_password2': 'IchangedTHEpassword#123'}
        # add 2 minutes to time to let min password age elapse
        StubDate.now = classmethod(
            lambda cls, timezone: datetime.now().replace(tzinfo=pytz.UTC)
                                  + relativedelta(minutes=+2)
        )
        response = self.client.post(url, form_data, follow=True)
        self.assertContains(response,
                            ("You can not use a password that is already used"
                             " in this application within password re-use interval"))
        self.user = User.objects.get(username="fred")  # get user again so that you can see password unchanged
        self.assertEquals(self.user.check_password("2ndChange#Pass"), True)

        # 4th password change - re-use password used in 1st
        form_data = {'old_password': '2ndChange#Pass',
                     'new_password1': 'IchangedTHEpassword#123',
                     'new_password2': 'IchangedTHEpassword#123'}
        # add 70 minutes to let password reuse restriction to elapse
        StubDate.now = classmethod(
            lambda cls, timezone: datetime.now().replace(tzinfo=pytz.UTC)
                                  + relativedelta(minutes=+70)
        )
        response = self.client.post(url, form_data, follow=True)
        self.assertContains(response, "Your password was updated.")
        self.user = User.objects.get(username="fred")  # get user again so that you can see password changed
        self.assertEquals(self.user.check_password("IchangedTHEpassword#123"), True)

        # add 12 minutes to time to expire current password
        StubDate.now = classmethod(
            lambda cls, timezone: datetime.now().replace(tzinfo=pytz.UTC)
                                  + relativedelta(minutes=+12)
        )
        self.client.logout()
        form_data = {'username': 'fred',
                     'password': 'IchangedTHEpassword#123'}
        response = self.client.post(reverse('login'), form_data, follow=True)
        self.assertContains(response,
                            ("Your password has expired, change password strongly recommended."))

    @override_switch('login', active=True)
    @mock.patch("apps.accounts.validators.datetime", StubDate)
    def test_password_expire_not_affect_staff(self):
        self.client.logout()
        # add 20 minutes to time to show staff is not effected
        StubDate.now = classmethod(
            lambda cls, timezone: datetime.now().replace(tzinfo=pytz.UTC)
                                  + relativedelta(minutes=+20)
        )
        form_data = {'username': 'staff',
                     'password': 'foobarfoobarfoobar'}
        response = self.client.post(reverse('login'), form_data, follow=True)
        # assert account dashboard page
        self.assertContains(response,
                            ("My Sandbox Apps"))
        self.assertContains(response,
                            ("The Developer Sandbox lets you register applications to get credentials"))

    def test_password_reuse_min_age_validator_args_check(self):
        with self.assertRaisesRegex(ValueError,
                                    (".*password_min_age < password_reuse_interval expected.*"
                                     "password_expire < password_reuse_interval expected.*"
                                     "password_min_age < password_expire expected.*")):
            PasswordReuseAndMinAgeValidator(60 * 60 * 24 * 30, 60 * 60 * 24 * 10, 60 * 60 * 24 * 20)
