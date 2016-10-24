import pytz
import random
import uuid

from datetime import datetime, timedelta
from django.utils import timezone

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
import boto3
from .emails import (send_password_reset_url_via_email,
                     send_activation_key_via_email,
                     mfa_via_email)


USER_CHOICES = (
    ('BEN', 'Beneficiary'),
    ('DEV', 'Developer'),
)

LOA_CHOICES = (
    ('0', 'LOA-0'),
    ('1', 'LOA-1'),
    ('2', 'LOA-2'),
    ('3', 'LOA-3'),
    ('4', 'LOA-4'),
)


QUESTION_1_CHOICES = (
    ('1', 'What is your favorite color?'),
    ('2', 'What is your favorite vegetable?'),
    ('3', 'What is your favorite movie?'),
)

QUESTION_2_CHOICES = (
    ('1', 'What was the name of your best friend from childhood?'),
    ('2', 'What was the name of your elementary school?'),
    ('3', 'What was the name of your favorite pet?'),
)

QUESTION_3_CHOICES = (
    ('1', 'What was the make of your first automobile?'),
    ('2', "What was your maternal grandmother's maiden name?"),
    ('3', "What was your paternal grandmother's maiden name?"),
)
MFA_CHOICES = (
    ('', 'None'),
    ('EMAIL', "Email"),
    ('SMS', "Text Message (SMS)"),
)


@python_2_unicode_compatible
class UserProfile(models.Model):
    user = models.OneToOneField(User)
    organization_name = models.CharField(max_length=255,
                                         blank=True,
                                         default='')
    loa = models.CharField(default='0',
                           choices=LOA_CHOICES,
                           max_length=5)
    user_type = models.CharField(default='DEV',
                                 choices=USER_CHOICES,
                                 max_length=5)
    access_key_id = models.CharField(max_length=20,
                                     blank=True)
    access_key_secret = models.CharField(max_length=40,
                                         blank=True)
    access_key_reset = models.BooleanField(
        blank=True,
        default=False,
        help_text=_('Check this box to issue a new access key. '
                    'Doing so invalidates the existing key.'),
    )

    create_applications = models.BooleanField(
        blank=True,
        default=False,
        help_text=_(
            'Check this to allow the account to register applications.'),
    )

    mfa_login_mode = models.CharField(
        blank=True,
        default="",
        max_length=5,
        choices=MFA_CHOICES,
    )

    mobile_phone_number = models.CharField(
        max_length=12,
        blank=True,
        help_text=_('US numbers only.'),
    )

    password_reset_question_1 = models.CharField(default='1',
                                                 choices=QUESTION_1_CHOICES,
                                                 max_length=1)
    password_reset_answer_1 = models.CharField(default='',
                                               blank=True,
                                               max_length=50)
    password_reset_question_2 = models.CharField(default='1',
                                                 choices=QUESTION_2_CHOICES,
                                                 max_length=1)
    password_reset_answer_2 = models.CharField(default='',
                                               blank=True,
                                               max_length=50)
    password_reset_question_3 = models.CharField(default='1',
                                                 choices=QUESTION_3_CHOICES,
                                                 max_length=1)
    password_reset_answer_3 = models.CharField(default='',
                                               blank=True,
                                               max_length=50)

    def __str__(self):
        name = '%s %s (%s)' % (self.user.first_name,
                               self.user.last_name,
                               self.user.username)
        return name

    def save(self, **kwargs):
        if not self.access_key_id or self.access_key_reset:
            self.access_key_id = random_key_id()
            self.access_key_secret = random_secret()
        self.access_key_reset = False
        super(UserProfile, self).save(**kwargs)


@python_2_unicode_compatible
class MFACode(models.Model):
    user = models.ForeignKey(User)
    uid = models.CharField(blank=True,
                           default=uuid.uuid4,
                           max_length=36, editable=False)
    tries_counter = models.IntegerField(default=0, editable=False)
    code = models.CharField(blank=True, max_length=4, editable=False)
    mode = models.CharField(max_length=5, default="",
                            choices=MFA_CHOICES)
    valid = models.BooleanField(default=True)
    expires = models.DateTimeField(blank=True)
    added = models.DateField(auto_now_add=True)

    def __str__(self):
        name = 'To %s via %s' % (self.user,
                                 self.mode)
        return name

    def endpoint(self):
        e = ""
        up = UserProfile.objects.get(user=self.user)
        if self.mode == "SMS" and up.mobile_phone_number:
            e = up.mobile_phone_number
        if self.mode == "EMAIL" and self.user.email:
            e = self.user.email
        return e

    def save(self, **kwargs):
        if not self.id:
            now = pytz.utc.localize(datetime.utcnow())
            expires = now + timedelta(days=1)
            self.expires = expires
            self.code = str(random.randint(1000, 9999))
            up = UserProfile.objects.get(user=self.user)
            if self.mode == "SMS" and \
               up.mobile_phone_number and \
               settings.SEND_SMS:
                # Send SMS to up.mobile_phone_number
                sns = boto3.client('sns',
                                   aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                   aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                   region_name='us-east-1')
                number = "+1%s" % (up.mobile_phone_number)
                sns.publish(
                    PhoneNumber=number,
                    Message="Your code is : %s" % (self.code),
                    MessageAttributes={
                        'AWS.SNS.SMS.SenderID': {
                            'DataType': 'String',
                            'StringValue': 'MySenderID'
                        }
                    }
                )
            elif self.mode == "SMS" and not up.mobile_phone_number:
                print("Cannot send SMS. No phone number on file.")
            elif self.mode == "EMAIL" and self.user.email:
                # "Send SMS to self.user.email
                mfa_via_email(self.user, self.code)
            elif self.mode == "EMAIL" and not self.user.email:
                print("Cannot send email. No email_on_file.")
            else:
                """No MFA code sent"""
                pass
        super(MFACode, self).save(**kwargs)


@python_2_unicode_compatible
class RequestInvite(models.Model):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    organization = models.CharField(max_length=150)
    email = models.EmailField(max_length=150)
    added = models.DateField(auto_now_add=True)
    user_type = models.CharField(default='BEN',
                                 choices=USER_CHOICES,
                                 max_length=5)

    def __str__(self):
        r = '%s %s' % (self.first_name, self.last_name)
        return r


@python_2_unicode_compatible
class Invitation(models.Model):
    code = models.CharField(max_length=10, unique=True)
    email = models.EmailField(blank=True)
    valid = models.BooleanField(default=True)
    added = models.DateField(auto_now_add=True)
    user_type = models.CharField(default='BEN',
                                 choices=USER_CHOICES,
                                 max_length=5)

    def __str__(self):
        return self.code

    def save(self, **kwargs):
        if self.valid:
            # send the verification email.
            registration_url = ''
            if self.user_type == "DEV":
                registration_url = settings.INVITE_DEVELOPER_REGISTRATION_URL
                invite_type = "Developer"
            else:
                registration_url = settings.INVITE_USER_REGISTRATION_URL
                invite_type = "User"
            msg = """
            <html>
            <head>
            </head>
            <body>
            Congratulations. You have been invited to join the
            %s %s community.<br>

            You may now register using this link: <a href='%s%s?invitation_code=%s&email=%s'>
            %s%s</a>.<br/>
            With the invitation code:
            <h2>%s</h2>

            - The %s Team
            </body>
            </html>
            """ % (settings.ORGANIZATION_NAME,
                   invite_type,
                   settings.HOSTNAME_URL,
                   registration_url,
                   self.code,
                   self.email,
                   settings.HOSTNAME_URL,
                   registration_url,
                   self.code,
                   settings.ORGANIZATION_NAME)
            if settings.SEND_EMAIL:
                subj = '[%s] %s Invitation ' \
                       'Code: %s' % (settings.ORGANIZATION_NAME,
                                     invite_type,
                                     self.code)

                msg = EmailMessage(subj,
                                   msg,
                                   settings.DEFAULT_FROM_EMAIL,
                                   [self.email])
                # Main content is now text/html
                msg.content_subtype = 'html'
                msg.send()

        super(Invitation, self).save(**kwargs)


@python_2_unicode_compatible
class ActivationKey(models.Model):
    user = models.ForeignKey(User)
    key = models.CharField(default=uuid.uuid4, max_length=40)
    expires = models.DateTimeField(blank=True)

    def __str__(self):
        return 'Key for %s expires at %s' % (self.user.username,
                                             self.expires)

    def save(self, **kwargs):
        self.signup_key = str(uuid.uuid4())

        now = pytz.utc.localize(datetime.utcnow())
        expires = now + timedelta(days=settings.SIGNUP_TIMEOUT_DAYS)
        self.expires = expires

        # send an email with reset url
        send_activation_key_via_email(self.user, self.key)
        super(ActivationKey, self).save(**kwargs)


@python_2_unicode_compatible
class ValidPasswordResetKey(models.Model):
    user = models.ForeignKey(User)
    reset_password_key = models.CharField(max_length=50, blank=True)
    # switch from datetime.now to timezone.now
    expires = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '%s for user %s expires at %s' % (self.reset_password_key,
                                                 self.user.username,
                                                 self.expires)

    def save(self, **kwargs):
        self.reset_password_key = str(uuid.uuid4())
        # use timezone.now() instead of datetime.now()
        now = timezone.now()
        expires = now + timedelta(minutes=1440)
        self.expires = expires

        # send an email with reset url
        send_password_reset_url_via_email(self.user, self.reset_password_key)
        super(ValidPasswordResetKey, self).save(**kwargs)


@python_2_unicode_compatible
class InvitesAvailable(models.Model):
    """ Stores BEN / DEV unused Invites """
    user_type = models.CharField(default='DEV',
                                 choices=USER_CHOICES,
                                 max_length=5)
    issued = models.IntegerField()
    available = models.IntegerField()
    last_issued = models.EmailField(blank=True)

    def __str__(self):
        u_t = self.user_type
        for k, v in USER_CHOICES:
            if self.user_type == k:
                u_t = v
        return '%s invites available for %s' % ((self.available - self.issued),
                                                u_t)


def random_key_id(y=20):
    return ''.join(random.choice('ABCDEFGHIJKLM'
                                 'NOPQRSTUVWXYZ') for x in range(y))


def random_secret(y=40):
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz'
                                 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                 '0123456789') for x in range(y))


def random_code(y=10):
    return ''.join(random.choice('ABCDEFGHIJKLM'
                                 'NOPQRSTUVWXYZ'
                                 '234679') for x in range(y))


def create_activation_key(user):
    # Create an new activation key and send the email.
    key = ActivationKey.objects.create(user=user)
    return key
