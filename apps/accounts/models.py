import pytz
import random
import uuid
from datetime import datetime, timedelta
from django.contrib.admin.models import LogEntry
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from .emails import (send_password_reset_url_via_email,
                     send_activation_key_via_email,
                     mfa_via_email, send_invite_to_create_account,
                     send_invitation_code_to_user,
                     notify_admin_of_invite_request)
import logging
from django.utils.crypto import pbkdf2
import binascii
from django.utils.translation import ugettext
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import CASCADE

ADDITION = 1
CHANGE = 2
DELETION = 3


logger = logging.getLogger('hhs_oauth_server.accounts')
admin_logger = logging.getLogger('admin_interface')


USER_CHOICES = (
    ('BEN', 'Beneficiary'),
    ('DEV', 'Developer'),
)


# Enrollment and Identity Proofing. NIST SP 800-63-A
# Level of Assurance - Legacy/Deprecated  See NIST SP 800-63-2
LOA_CHOICES = (
    ('', 'Undefined'),
    ('1', 'LOA-1'),
    ('2', 'LOA-2'),
    ('3', 'LOA-3'),
    ('4', 'LOA-4'),
)

# Enrollment and Identity Proofing. NIST SP 800-63-3 A
# Identity assurance level
IAL_CHOICES = (
    ('', 'Undefined'),
    ('0', 'IAL0'),
    ('1', 'IAL1'),
    ('2', 'IAL2'),
    ('3', 'IAL3'),
)


# Enrollment and Identity Proofing. NIST SP 800-63-33 B
# Authenticator Assurance Level
AAL_CHOICES = (
    ('', 'Undefined'),
    ('0', 'AAL0'),
    ('1', 'AAL1'),
    ('2', 'AAL2'),
    ('3', 'AAL3'),
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
)

ISSUE_INVITE = (
    ('', 'Not Set'),
    ('YES', 'Yes - Send Invite'),
    ('NO', 'NO - Do not send invite'),
    ('DONE', 'Invite has been sent')
)


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=CASCADE, )
    organization_name = models.CharField(max_length=255,
                                         blank=True,
                                         default='')
    loa = models.CharField(default='2',
                           choices=LOA_CHOICES,
                           max_length=1,
                           blank=True,
                           verbose_name="Level of Assurance",
                           help_text="Legacy and Deprecated. Using IAL AAL is recommended.")

    ial = models.CharField(default='2',
                           choices=IAL_CHOICES,
                           max_length=1,
                           blank=True,
                           verbose_name="Identity Assurance Level",
                           help_text="See NIST SP 800 63 3A for definitions.")

    aal = models.CharField(default='1',
                           choices=AAL_CHOICES,
                           max_length=1,
                           blank=True,
                           verbose_name="Authenticator Assurance Level",
                           help_text="See NIST SP 800 63 3 B for definitions.")

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

    def vot(self):
        r = "P%s" % (self.ial)
        if self.aal in ('1', '2'):
            r = r + "Cc"
        if self.aal == '2':
            r = r + "Cb"
        return r

    def save(self, **kwargs):
        if self.mfa_login_mode:
            self.aal = '2'

        if not self.access_key_id or self.access_key_reset:
            self.access_key_id = random_key_id()
            self.access_key_secret = random_secret()
        self.access_key_reset = False
        super(UserProfile, self).save(**kwargs)


class MFACode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, )
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
        if self.mode == "EMAIL" and self.user.email:
            e = self.user.email
        return e

    def save(self, **kwargs):
        if not self.id:
            now = pytz.utc.localize(datetime.utcnow())
            expires = now + timedelta(days=1)
            self.expires = expires
            self.code = str(random.randint(1000, 9999))
            if self.mode == "EMAIL" and self.user.email:
                # "Send to self.user.email
                mfa_via_email(self.user, self.code)
            elif self.mode == "EMAIL" and not self.user.email:
                logger.info("Cannot send email. No email_on_file.")

        super(MFACode, self).save(**kwargs)


class RequestInvite(models.Model):
    user_type = models.CharField(max_length=3, choices=USER_CHOICES,
                                 default="DEV")
    first_name = models.CharField(max_length=150, default="")
    last_name = models.CharField(max_length=150, default="")
    organization = models.CharField(max_length=150, blank=True, default="")
    email = models.EmailField(max_length=150)
    added = models.DateField(auto_now_add=True)
    issue_invite = models.CharField(max_length=4,
                                    choices=ISSUE_INVITE,
                                    default="")
    invite_sent = models.BooleanField(default=False)

    def __str__(self):
        r = '%s %s as a %s' % (self.first_name, self.last_name, self.user_type)
        return r

    def save(self, commit=True, **kwargs):
        if commit:
            logger.info(
                "Invite requested for {} {} ({})".format(
                    self.first_name,
                    self.last_name,
                    self.email))
            notify_admin_of_invite_request(self)

            if self.issue_invite == "YES" and self.invite_sent is False:
                # Add record to Invitation
                object, created = Invitation.objects.update_or_create(email=self.email,
                                                                      code=random_code())
                if created:
                    self.issue_invite = "DONE"
                    self.invite_sent = True
                else:
                    self.issue_invite = ""

            super(RequestInvite, self).save(**kwargs)

    class Meta:
        verbose_name = "Invite Request"


class UserRegisterCode(models.Model):
    user_id_hash = models.CharField(max_length=64, blank=True, default="")
    code = models.CharField(max_length=30, db_index=True)
    valid = models.BooleanField(default=False, blank=True)
    username = models.CharField(max_length=40)
    email = models.EmailField(max_length=150)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, null=True, blank=True)
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
        hostname = getattr(settings, 'HOSTNAME_URL', 'http://localhost:8000')

        if "http://" in hostname.lower():
            pass
        elif "https://" in hostname.lower():
            pass
        else:
            logger.debug("HOSTNAME_URL [%s] "
                         "does not contain http or https prefix. "
                         "Issuer:%s" % (settings.HOSTNAME_URL, hostname))
            # no http/https prefix in HOST_NAME_URL so we add it
            hostname = "https://%s" % (hostname)
        return "%s%s?username=%s&code=%s" % (hostname,
                                             reverse('user_code_register'),
                                             self.username, self.code)

    def save(self, commit=True, **kwargs):
        if commit:
            self.user_id_hash = binascii.hexlify(pbkdf2(self.user_id_hash,
                                                        get_user_id_salt(),
                                                        settings.USER_ID_ITERATIONS)).decode("ascii")
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
        hostname = getattr(settings, 'HOSTNAME_URL', 'http://localhost:8000')

        if "http://" in hostname.lower():
            pass
        elif "https://" in hostname.lower():
            pass
        else:
            logger.debug("HOSTNAME_URL [%s] "
                         "does not contain http or https prefix. "
                         "Issuer:%s" % (settings.HOSTNAME_URL, hostname))
            # no http/https prefix in HOST_NAME_URL so we add it
            hostname = "https://%s" % (hostname)
        return "%s%s" % (hostname,
                         reverse('accounts_create_account'))

    def save(self, commit=True, **kwargs):
        if commit:
            if self.valid:
                # send the invitation verification email.
                send_invite_to_create_account(self)
                logger.info("Invitation sent to {}".format(self.email))

            super(Invitation, self).save(**kwargs)


class ActivationKey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE,)
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


class ValidPasswordResetKey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE,)
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
            send_password_reset_url_via_email(
                self.user, self.reset_password_key)
            logger.info("Password reset sent to {} ({})".format(self.user.username,
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


@receiver(post_save)
def export_admin_log(sender, instance, **kwargs):

    msg = ""
    if isinstance(instance, LogEntry):
        if instance.action_flag == ADDITION:
            msg = ugettext('User "%(user)s" added %(content_type)s object. "%(object)s" added at %(action_time)s') % {
                'user': instance.user,
                'content_type': instance.get_edited_object,
                'object': instance.object_repr,
                'action_time': instance.action_time}

        elif instance.action_flag == CHANGE:
            msg = ugettext('User "%(user)s" changed %(content_type)s object. "%(object)s" - %(changes)s at %(action_time)s') % {
                'user': instance.user,
                'content_type': instance.content_type,
                'object': instance.object_repr,
                'changes': instance.change_message,
                'action_time': instance.action_time}

        elif instance.action_flag == DELETION:
            msg = ugettext('User  "%(user)s" deleted %(content_type)s object. "%(object)s" deleted at %(action_time)s') % {
                'user': instance.user,
                'content_type': instance.content_type,
                'object': instance.object_repr,
                'action_time': instance.action_time}

        admin_logger.info(msg)


def get_user_id_salt(salt=settings.USER_ID_SALT):
    """
    Assumes `USER_ID_SALT` is a hex encoded value. Decodes the salt val,
    returning binary data represented by the hexadecimal string.

    :param: salt
    :return: bytes
    """
    return binascii.unhexlify(salt)
