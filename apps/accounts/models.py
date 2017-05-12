from __future__ import absolute_import
from __future__ import unicode_literals
import pytz
import random
import uuid
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
import boto3
from django.core.urlresolvers import reverse
from .emails import (send_password_reset_url_via_email,
                     send_activation_key_via_email,
                     mfa_via_email, send_invite_to_create_account,
                     send_invitation_code_to_user,
                     notify_admin_of_invite_request)
from collections import OrderedDict
import logging

logger = logging.getLogger('hhs_oauth_server.accounts')

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
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    organization_name = models.CharField(max_length=255,
                                         blank=True,
                                         default='')
    loa = models.CharField(default='0',
                           choices=LOA_CHOICES,
                           max_length=5)
    user_type = models.CharField(default='DEV',
                                 choices=USER_CHOICES,
                                 max_length=5)

    remaining_user_invites = models.IntegerField(default=0)
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

    authorize_applications = models.BooleanField(
        blank=True,
        default=False,
        help_text=_(
            'Check this to allow the account to authorize applications.'),
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

    def name(self):
        if self.organization_name:
            return self.organization_name
        else:
            name = '%s %s' % (self.user.first_name, self.user.last_name)
        return name

    def save(self, **kwargs):
        if not self.access_key_id or self.access_key_reset:
            self.access_key_id = random_key_id()
            self.access_key_secret = random_secret()
        self.access_key_reset = False
        super(UserProfile, self).save(**kwargs)


@python_2_unicode_compatible
class MFACode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
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
                sns = boto3.client(
                    'sns',
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
    organization = models.CharField(max_length=150, blank=True)
    email = models.EmailField(max_length=150)
    added = models.DateField(auto_now_add=True)

    def __str__(self):
        r = '%s %s' % (self.first_name, self.last_name)
        return r

    def save(self, commit=True, **kwargs):
        if commit:
            logger.info(
                "Invite requested for {} {} ({})".format(
                    self.first_name,
                    self.last_name,
                    self.email))
            notify_admin_of_invite_request(self)
            super(RequestInvite, self).save(**kwargs)

    class Meta:
        verbose_name = "Invite Request"


@python_2_unicode_compatible
class UserRegisterCode(models.Model):
    code = models.CharField(max_length=30)
    username = models.CharField(max_length=40)
    email = models.EmailField(max_length=150)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    sent = models.BooleanField(default=False, editable=False)
    used = models.BooleanField(default=False)
    resend = models.BooleanField(default=False,
                                 help_text="Check to resend")
    added = models.DateField(auto_now_add=True)

    def __str__(self):
        r = '%s %s' % (self.first_name, self.last_name)
        return r

    def name(self):
        r = '%s %s' % (self.first_name, self.last_name)
        return r

    def url(self):
        return "%s%s?username=%s&code=%s" % (settings.HOSTNAME_URL,
                                             reverse('user_code_login'),
                                             self.username, self.code)

    def save(self, commit=True, **kwargs):
        if commit:
            if self.sender:
                up = UserProfile.objects.get(user=self.sender)
                if self.sent is False:
                    if up.remaining_user_invites > 0:
                        up.remaining_user_invites -= 1
                        up.save()
                        send_invitation_code_to_user(self)
                        self.sent = True
                        self.resend = False
                if self.sent is True and self.resend is True:
                    send_invitation_code_to_user(self)
                    self.sent = True
                    self.resend = False
            else:
                if self.sent is False or self.resend is True:
                    send_invitation_code_to_user(self)
                    self.sent = True
                    self.resend = False
            super(UserRegisterCode, self).save(**kwargs)


@python_2_unicode_compatible
class Invitation(models.Model):
    code = models.CharField(max_length=10, unique=True)
    email = models.EmailField(blank=True)
    valid = models.BooleanField(default=True)
    added = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Developer Invitation"

    def __str__(self):
        return self.code

    def url(self):
        return "%s%s" % (settings.HOSTNAME_URL,
                         reverse('accounts_create_account'))

    def save(self, commit=True, **kwargs):
        if commit:
            if self.valid:
                # send the invitation verification email.
                send_invite_to_create_account(self)
                logger.info("Invitation sent to {}".format(self.email))

            super(Invitation, self).save(**kwargs)


@python_2_unicode_compatible
class ActivationKey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    reset_password_key = models.CharField(max_length=50, blank=True)
    # switch from datetime.now to timezone.now
    expires = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '%s for user %s expires at %s' % (self.reset_password_key,
                                                 self.user.username,
                                                 self.expires)

    def save(self, commit=True, **kwargs):
        if commit:
            self.reset_password_key = str(uuid.uuid4())
            # use timezone.now() instead of datetime.now()
            now = timezone.now()
            expires = now + timedelta(minutes=1440)
            self.expires = expires

            # send an email with reset url
            send_password_reset_url_via_email(self.user, self.reset_password_key)
            logger.info("Password reset sent to Invitation sent to {} ({})".format(self.user.username,
                                                                                   self.user.email))
            super(ValidPasswordResetKey, self).save(**kwargs)


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


@python_2_unicode_compatible
class EmailWebhook(models.Model):
    email = models.EmailField(max_length=150, default="", blank=True)
    status = models.CharField(max_length=30, default="", blank=True)
    details = models.TextField(max_length=2048, default="", blank=True)
    added = models.DateField(auto_now_add=True)

    def __str__(self):
        r = '%s: %s' % (self.email, self.status)
        return r

    def save(self, commit=True, request_body="", **kwargs):
        if commit:
            if request_body:
                whr = json.loads(str(request_body.decode('utf-8')),
                                 object_pairs_hook=OrderedDict)
                message = json.loads(whr["Message"])
                self.status = message['notificationType']
                if self.status == "Bounce":
                    self.email = message['bounce'][
                        'bouncedRecipients'][0]["emailAddress"]
                if self.status == "Complaint":
                    self.email = message['complainedRecipients'][0]["emailAddress"]
                if self.status == "Delivery":
                    self.email = message['mail']["destination"][0]
                self.details = request_body
                logger.info("Sent email {} status is {}.".format(self.email, self.status))
                super(EmailWebhook, self).save(**kwargs)
