#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: test_invitations
Created: 8/24/16 12:17 AM

File created by: ''
"""
import logging
from django.test import TestCase
# from django.test.client import Client
from ..models import InvitesAvailable
from ..views.core import issue_invite

logger = logging.getLogger('hhs_server.%s' % __name__)


class InvitationTest(TestCase):
    """ Test invitations """

    def test_good_developer(self):
        iab = InvitesAvailable.objects.create(user_type="BEN",
                                              issued=0,
                                              available=3)

        iad = InvitesAvailable.objects.create(user_type="DEV",
                                              issued=0,
                                              available=3)

        logger.debug("Ben: %s" % iab)
        logger.debug("Dev: %s" % iad)
        result = issue_invite("Developer1@dev.com", user_type="DEV")

        expect = "Developer1@dev.com"

        logger.debug("Result:%s" % result)

        self.assertEqual(result.email, expect)
