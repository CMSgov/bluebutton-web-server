#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
BlueButtonFHIR_API
FILE: signals.py
Created: 2/24/16 1:23 PM

__author__ = 'Mark Scrimshire:@ekivemark'


"""
import json
import logging

# from collections import OrderedDict

# from django.conf import settings

from django.dispatch import receiver
from django.db.models.signals import post_save
from oauth2_provider.models import AccessToken

logger = logging.getLogger('hhs_server.%s' % __name__)

# from appmgmt.utils import write_fhir, build_fhir_id
# from fhir_io_hapi.utils import fhir_datetime


@receiver(post_save, sender=AccessToken)
def write_consent(sender, **kwargs):
    print("\n==============")
    print("\nIn the post_save")
    logger.debug("\n=============================================\n"
                 "Model post_save:%s" % sender)
    logger.debug('\nSaved: {}'.format(kwargs['instance'].__dict__))

    A_Tkn = kwargs['instance'].__dict__

    # Write Consent JSON

    # Write fhir_Consent

    friendly_language = "Beneficiary (%s) gave " \
                        "[%s] permission to application " \
                        "(%s)" % (str(A_Tkn['user_id']),
                                  A_Tkn['scope'],
                                  A_Tkn['_application_cache'].fhir_reference)
    body = {"text": friendly_language}
    result = "pending"

    logger.debug("\nA_Tkn:%s\nBody:%s"
                 "\njson:%s\nResult:%s" % (A_Tkn,
                                           body,
                                           json.dumps(body),
                                           result))
