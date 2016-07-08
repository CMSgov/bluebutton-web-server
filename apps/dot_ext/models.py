from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import jwt
import hashlib
import logging
import requests
import datetime

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone

from requests.exceptions import ConnectionError, TooManyRedirects, Timeout
from oauth2_provider.models import AbstractApplication
from poetri.verify_poet import verify_poet

from apps.capabilities.models import ProtectedCapability


logger = logging.getLogger('hhs_server.%s' % __name__)


@python_2_unicode_compatible
class Endorsement(models.Model):
    title = models.CharField(max_length=255,
                             default='')
    jwt = models.TextField(max_length=10240,
                           default='')
    iss = models.CharField(max_length=512,
                           default='',
                           verbose_name='Issuer',
                           help_text='Must contain a FQDN',
                           editable=False)
    iat = models.DateTimeField(verbose_name='Issued At',
                               editable=False)
    exp = models.DateTimeField(verbose_name='Expires',
                               editable=False)

    def __str__(self):
        return self.title

    def signature_verified(self):
        url = 'http://%s/.wellknown/poet.pem' % (self.iss)

        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                payload = verify_poet(self.jwt, r.text)
                if 'iss' in payload:
                    return True
        except ConnectionError:
            pass
        except TooManyRedirects:
            pass
        except Timeout:
            pass

        url = 'http://%s/.wellknown/poet.jwks' % (self.iss)
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                payload = verify_poet(self.jwt, r.text)
                if 'iss' in payload:
                    return True
        except ConnectionError:
            pass
        except TooManyRedirects:
            pass
        except Timeout:
            pass

        try:
            url = 'https://%s/.wellknown/poet.pem' % (self.iss)
            r = requests.get(url, verify=False, timeout=1)
            if r.status_code == 200:
                payload = verify_poet(self.jwt, r.text)
                if 'iss' in payload:
                    return True
        except ConnectionError:
            pass
        except TooManyRedirects:
            pass
        except Timeout:
            pass

        try:
            url = 'https://%s/.wellknown/poet.jwks' % (self.iss)
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                payload = verify_poet(self.jwt, r.text)
                if 'iss' in payload:
                    return True
        except ConnectionError:
            pass
        except TooManyRedirects:
            pass
        except Timeout:
            pass

        return False

    def payload(self):
        payload = jwt.decode(self.jwt, verify=False)
        return payload

    def is_expired(self):
        now = timezone.now()
        if self.iat > now:
            return True
        return False

    def save(self, commit=True, **kwargs):
        if commit:
            payload = jwt.decode(self.jwt, verify=False)
            self.iss = payload['iss']
            self.iat = datetime.datetime.fromtimestamp(int(payload['iat'])).strftime('%Y-%m-%d %H:%M:%S')
            self.exp = datetime.datetime.fromtimestamp(int(payload['exp'])).strftime('%Y-%m-%d %H:%M:%S')
            super(Endorsement, self).save(**kwargs)


class Application(AbstractApplication):
    scope = models.ManyToManyField(ProtectedCapability)
    endorsements = models.ManyToManyField(Endorsement, blank=True)
    agree = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('oauth2_provider:detail', args=[str(self.id)])


class ExpiresInManager(models.Manager):
    """
    Provide a `set_expires_in` and `get_expires_in` methods that
    work as a cache. The key is generated from `client_id` and `user_id`.
    """

    @staticmethod
    def make_key(client_id, user_id):
        """
        Generate a unique key using client_id and user_id args.
        """
        arg = '%s_%s' % (client_id, user_id)
        # Python 3 - avoid TypeError: Unicode-objects
        # must be encoded before hashing
        if sys.version_info > (3, 2):
            arg = arg.encode('utf-8')
        return hashlib.sha256(arg).hexdigest()

    def set_expires_in(self, client_id, user_id, expires_in):
        """
        Set the expires_in value for the key generated with
        client_id and user_id.
        """
        key = self.make_key(client_id, user_id)
        instance, _ = self.update_or_create(
            key=key,
            defaults={'expires_in': expires_in})

    def get_expires_in(self, client_id, user_id):
        """
        Return the expires_in value for the key generated with
        client_id and user_id. Returns None when the key is not
        found.
        """
        key = self.make_key(client_id, user_id)
        try:
            return self.get(key=key).expires_in
        except self.model.DoesNotExist:
            return None


class ExpiresIn(models.Model):
    """
    This model is used to save the expires_in value selected
    in the allow form view. Then it can be queried when the token is
    issued to the user.
    """
    key = models.CharField(max_length=64, unique=True)
    expires_in = models.IntegerField()

    objects = ExpiresInManager()
