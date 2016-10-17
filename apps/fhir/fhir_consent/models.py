from collections import OrderedDict

# from datetime import datetime
from django.conf import settings
from django.db import models
from django.utils import timezone

from jsonfield import JSONField

# Create your models here.


class fhir_Consent(models.Model):
    """ Store User:application consent in fhir format
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    application = models.ForeignKey(settings.OAUTH2_PROVIDER_APPLICATION_MODEL)
    consent = JSONField(load_kwargs={'object_pairs_hook': OrderedDict})
    created = models.DateTimeField(blank=True, null=True)
    revoked = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)
    key = models.TextField(max_length=250, blank=True, null=True)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        # Update the key field
        self.key = self.user.username + ":" + self.application.name + "["
        self.key += self.created.strftime('%Y-%m-%dT%H:%M.%S') + "]"

        if self.valid_until:
            # print("\nChecking valid_until"
            #       " still valid:%s\nType:%s" % (self.valid_until,
            #                                   type(self.valid_until)))
            if self.valid_until <= timezone.now():
                if not self.revoked:
                    self.revoked = self.valid_until

        return super(fhir_Consent, self).save(*args, **kwargs)

    def revoke_consent(self, confirm=False, *args, **kwargs):
        if confirm is True:
            if not self.revoked:
                self.revoked = timezone.now()

        return super(fhir_Consent, self).save(*args, **kwargs)

    def status(self):
        consent_status = None
        if self.revoked:
            consent_status = "REVOKED"
        else:
            consent_status = "VALID"
        return consent_status

    def granted(self):
        if self.created and self.revoked:
            valid = False
        else:
            valid = True
        return valid

    def __str__(self):
        name = '%s %s (%s)' % (self.user.first_name,
                               self.user.last_name,
                               self.user.username)
        return ("%s:%s" % (name, self.application.name))

    def __unicode__(self):
        name = '%s %s (%s)' % (self.user.first_name,
                               self.user.last_name,
                               self.user.username)
        return ("%s:%s" % (name, self.application.name))
