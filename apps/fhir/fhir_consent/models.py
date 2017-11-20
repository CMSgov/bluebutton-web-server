from __future__ import absolute_import
from __future__ import unicode_literals
from django.conf import settings
from django.db import models
from django.utils.timezone import now
import logging

__author__ = "Mark Scrimshire and Alan Viars"

logger = logging.getLogger('hhs_server.%s' % __name__)


class Consent(models.Model):
    """ Store User:application consent in fhir format
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    application = models.ForeignKey(settings.OAUTH2_PROVIDER_APPLICATION_MODEL)
    consent = models.TextField(blank=True, default="")
    created = models.DateTimeField(default=now)
    modified = models.DateTimeField(auto_now=True)
    # choice = CREATED (2) | REVOKED (0) | UPDATED (4)

    def save(self, *args, **kwargs):
        """ On save, update timestamps """

        return super(Consent, self).save(*args, **kwargs)

    def myuser(self):
        return "%s %s" % (self.user.first_name, self.user.last_name)

    def __str__(self):
        name = '%s %s (%s)' % (self.user.first_name,
                               self.user.last_name,
                               self.user.username)
        return ("%s:%s" % (name, self.application.name))
