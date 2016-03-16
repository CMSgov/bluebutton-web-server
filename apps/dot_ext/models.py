from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from oauth2_provider.models import AbstractApplication

from apps.capabilities.models import ProtectedCapability


logger = logging.getLogger('hhs_server.%s' % __name__)


@python_2_unicode_compatible
class Endorsement(models.Model):
    title   = models.TextField(max_length=256, default="")
    iss     = models.TextField(max_length=512, default="", verbose_name="Issuer",
                               help_text="Must contain a QDN")
    jws     = models.TextField(max_length=10240, default="")

    def __str__(self):
        return self.title


class Application(AbstractApplication):
    scope                  = models.ManyToManyField(ProtectedCapability)
    endorsements           = models.ManyToManyField(Endorsement, blank=True)
    agree                  = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('oauth2_provider:detail', args=[str(self.id)])
