#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: test_invitations
Created: 8/24/16 12:17 AM

File created by: ''
"""
# import logging
from django.test import TestCase
# from django.test.client import Client
from django.contrib.auth.models import User, Group
from ..models import Invitation, UserRegisterCode, UserProfile
from django.core import mail


class SendDeveloperInviteTestCase(TestCase):
    """
    Test Sending and invite to create an account
    """

    def setUp(self):
        Invitation.objects.create(code='1234', email='fred@example.com')

    def test_email_was_sent(self):
        self.assertEquals(len(mail.outbox), 1)


class SendUserInviteTestCase(TestCase):
    """
    Test Sending and invite to create an account
    """

    def setUp(self):
        self.u = User.objects.create_user(username="fred",
                                          first_name="Fred",
                                          last_name="Flinstone",
                                          email='fred@example.com',
                                          password="foobar",)
        # User has only one invite to send.
        self.up = UserProfile.objects.create(user=self.u,
                                             user_type="DEV",
                                             create_applications=True,
                                             remaining_user_invites=1)
        Group.objects.create(name='BlueButton')

    def test_email_was_sent(self):
        """Invite should be sent"""
        up = UserProfile.objects.get(user=self.u)
        self.assertEquals(up.remaining_user_invites, 1)
        UserRegisterCode.objects.create(sender=self.u,
                                        first_name="Fred2",
                                        last_name="Flinstone2",
                                        code='4567',
                                        email='fred2@example.com')
        """One email sent"""
        self.assertEquals(len(mail.outbox), 1)
        up = UserProfile.objects.get(user=self.u)

        """Invites should now be depleted and another email should NOT be sent"""
        up = UserProfile.objects.get(user=self.u)
        self.assertEquals(up.remaining_user_invites, 0)
        UserRegisterCode.objects.create(sender=self.u,
                                        first_name="Fred",
                                        last_name="Flinstone",
                                        code='1234',
                                        email='fred2@example.com')

        """Still should be only one sent since user has no remaining invites."""
        self.assertEquals(len(mail.outbox), 1)
