#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
BlueButtonFHIR_API
FILE: signals.py
Created: 2/24/16 1:23 PM

__author__ = 'Mark Scrimshire:@ekivemark'

Requires entry in apps.py and __init__.py to enable write_consent

"""
from __future__ import absolute_import
from __future__ import unicode_literals
import logging

# from collections import OrderedDict
from django.utils import timezone

# from django.conf import settings
from oauth2_provider.models import AccessToken

from django.dispatch import receiver
from django.db.models.signals import post_save

from apps.fhir.build_fhir.utils.utils_fhir_dt import (dt_period,
                                                      dt_instant)
from apps.fhir.fhir_consent.views import rt_consent_directive_activate
from apps.fhir.fhir_consent.models import fhir_Consent

logger = logging.getLogger('hhs_server.%s' % __name__)

# from appmgmt.utils import write_fhir, build_fhir_id
# from fhir_io_hapi.utils import fhir_datetime


@receiver(post_save, sender=AccessToken)
def write_consent(sender, **kwargs):
    # logger.debug("\n=============================================\n"
    #              "Model post_save:%s" % sender)
    # logger.debug('\nSaved: {}'.format(kwargs['instance'].__dict__))

    A_Tkn = kwargs['instance'].__dict__

    # print("\n\nKWARGS:%s" % kwargs)
    # Write Consent JSON

    # Write fhir_Consent
    # print("\n\nA_Tkn:%s\n\n" % A_Tkn)
    A_Usr = A_Tkn['_user_cache']

    A_App = A_Tkn['_application_cache']
    # print("App:%s" % A_App)
    # print("App Name:%s" % A_App.name)
    A_Appname = A_App.name

    friendly_language = "Beneficiary (%s) gave " \
                        "(%s) permission to " \
                        "application:%s." % (A_Tkn['_user_cache'],
                                              A_Tkn['scope'],
                                              A_Appname)

    consent_now = timezone.now()
    # NOTE: dt_instant and dt_period create string representations of date
    instant_now = dt_instant(consent_now)
    instant_until = dt_instant(A_Tkn['expires'])
    oauth_period = dt_period(instant_now, instant_until)

    consent = rt_consent_directive_activate(A_Usr,
                                            A_App.name,
                                            friendly_language,
                                            oauth_period,
                                            A_Tkn['scope'])

    try:
        f_c = fhir_Consent.objects.get(user=A_Usr, application=A_App)
        created = False
    except fhir_Consent.DoesNotExist:
        f_c = fhir_Consent()
        f_c.user = A_Usr
        f_c.application = A_App
        f_c.consent = consent
        f_c.valid_until = A_Tkn['expires']

        f_c.save()
        created = True

    if created:
        pass
    else:
        vid = int(f_c.consent['meta']['versionId'])
        vid += 1
        consent['meta']['versionId'] = str(vid)

        f_c.consent = consent
        f_c.revoked = None
        f_c.valid_until = A_Tkn['expires']
        f_c.save()

    return
