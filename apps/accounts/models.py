import pytz
import random
import uuid

from datetime import datetime, timedelta

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from .emails import send_password_reset_url_via_email, send_activation_key_via_email


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

    def __str__(self):
        return self.code

    def save(self, **kwargs):
        if self.valid:
            # send the verification email.
            msg = """
            <html>
            <head>
            </head>
            <body>
            Congratulations. You have been invited to join the
            OAuth2 Server Alpha.<br>

            You may now <a href='%s'>register</a> with the invitation code:

            <h2>%s</h2>

            - The Team
            </body>
            </html>
            """ % (settings.HOSTNAME_URL, self.code,)
            if settings.SEND_EMAIL:
                subj = '[%s] Invitation ' \
                       'Code: %s' % (settings.ORGANIZATION_NAME,
                                     self.code)

                msg = EmailMessage(subj,
                                   msg,
                                   settings.EMAIL_HOST_USER,
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
    expires = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return '%s for user %s expires at %s' % (self.reset_password_key,
                                                 self.user.username,
                                                 self.expires)

    def save(self, **kwargs):
        self.reset_password_key = str(uuid.uuid4())
        now = datetime.now()
        expires = now + timedelta(minutes=1440)
        self.expires = expires

        # send an email with reset url
        send_password_reset_url_via_email(self.user, self.reset_password_key)
        super(ValidPasswordResetKey, self).save(**kwargs)


def random_key_id(y=20):
    return ''.join(random.choice('ABCDEFGHIJKLM'
                                 'NOPQRSTUVWXYZ') for x in range(y))


def random_secret(y=40):
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz'
                                 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                 '0123456789') for x in range(y))


def create_activation_key(user):
    # Create an new activation key and send the email.
    key = ActivationKey.objects.create(user=user)
    return key
