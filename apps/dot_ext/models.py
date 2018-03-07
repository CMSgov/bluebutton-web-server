from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import hashlib
import logging

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from apps.capabilities.models import ProtectedCapability
from oauth2_provider.models import AbstractApplication
from django.conf import settings

from apps.dot_ext.oauth2_validators import validate_uris

logger = logging.getLogger('hhs_server.%s' % __name__)


class Application(AbstractApplication):
    scope = models.ManyToManyField(ProtectedCapability)
    agree = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    op_tos_uri = models.CharField(default="", blank=True, max_length=512)
    op_policy_uri = models.CharField(default="", blank=True, max_length=512)
    client_uri = models.CharField(default="", blank=True, max_length=512, verbose_name="Client URI",
                                  help_text="This is typically a homepage for the application.")
    help_text = _('Allowed URIs listed, space or new line separated. '
                  'Including ??00000000:// for mobile native applications')
    redirect_uris = models.TextField(help_text=help_text,
                                     validators=[validate_uris], blank=True)
    logo_uri = models.CharField(
        default="", blank=True, max_length=512, verbose_name="Logo URI")
    tos_uri = models.CharField(
        default="", blank=True, max_length=512, verbose_name="Client's Terms of Service URI")
    policy_uri = models.CharField(default="", blank=True, max_length=512, verbose_name="Client's Policy URI",
                                  help_text="This can be a model privacy notice or other policy document.")
    software_id = models.CharField(default="", blank=True, max_length=128,
                                   help_text="A unique identifier for an application defined by its creator.")
    contacts = models.TextField(default="", blank=True, max_length=512,
                                verbose_name="Client's Contacts",
                                help_text="This is typically an email")
    active = models.BooleanField(default=True)

    def scopes(self):
        mylist = []
        for s in self.scope.all():
            mylist.append(s.slug)
        return " ".join(mylist).strip()

    def get_absolute_url(self):
        return reverse('oauth2_provider:detail', args=[str(self.id)])

    def save(self, commit=True, **kwargs):
        if commit:
            # Write the TOS that the app developer agreed to.
            self.op_tos_uri = settings.TOS_URI
            super(Application, self).save(**kwargs)
            logmsg = "%s agreed to %s for the application %s on %s" % (self.user, self.op_tos_uri,
                                                                       self.name, self.updated)
            logger.info(logmsg)


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

