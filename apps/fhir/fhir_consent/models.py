from collections import OrderedDict

# from datetime import datetime
from django.conf import settings
from django.db import models
from django.utils import timezone

from jsonfield import JSONField

CONSENT_STATE = (
    ("0", "REVOKED"),
    ("2", "CREATED"),
    ("4", "UPDATED"),
)
# e.g. state = "2" , value = "CREATED"
# v = dict(CONSENT_STATE)[state]
# CONSENT_STATE_FLIP = {value: key for key, value in CONSENT_STATE}
# k = dict(CONSENT_STATE_FLIP[value]


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
    state = models.CharField(max_length=1,
                             choices=CONSENT_STATE,
                             blank=True,
                             null=True,
                             default="2")
    # choice = CREATED (2) | REVOKED (0) | UPDATED (4)

    def save(self, *args, **kwargs):
        """ On save, update timestamps """
        if not self.id:
            self.created = timezone.now()
            self.state = "2"
        else:
            self.state = "4"

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
                # CONSENT_STATE = (
                #     ("0", "REVOKED"),
                #     ("2", "CREATED"),
                #     ("4", "UPDATED"),
                # )

                self.state = "0"

        return super(fhir_Consent, self).save(*args, **kwargs)

    def status(self):
        consent_state = None

        # CONSENT_STATE = (
        #     ("0", "REVOKED"),
        #     ("2", "CREATED"),
        #     ("4", "UPDATED"),
        # )

        if self.revoked and self.state == "0":
            consent_state = dict(CONSENT_STATE)[self.state]
        else:
            consent_state = dict(CONSENT_STATE)[self.state]

        return consent_state

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
