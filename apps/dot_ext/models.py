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
                               help_text= "Must contain a QDN")
    jws     = models.TextField(max_length=10240, default="")

    def __str__(self):
        return self.title


class Application(AbstractApplication):
    scope                  = models.ManyToManyField(ProtectedCapability)
    endorsements           = models.ManyToManyField(Endorsement, blank=True)
    agree                  = models.BooleanField(default=False)

    _messages = {
        "resource_allowed": "application '%s': access to resource '%s %s' allowed",
        "resource_forbidden": "application '%s': access to resource '%s %s' forbidden",
    }

    def get_absolute_url(self):
        return reverse('dote_detail', args=[str(self.id)])

    def allow_resource(self, method, path):
        """
        Return True when this applications has capability to allow
        request to `path` with method `method`.
        """
        logger.debug("application '%s': checking access to resource '%s %s' is allowed",
                     self.name, method, path)

        for scope in self.scope.all():
            resources = scope.resources_as_dict()
            logger.debug("application '%s': checking access with scope '%s'", self.name, resources)
            # TODO: should we normalize path, here?? trailing slash??
            if path in resources.get(method):
                logger.info(self._messages['resource_allowed'], self.name, method, path)
                return True

        logger.info(self._messages['resource_forbidden'], self.name, method, path)
        return False
