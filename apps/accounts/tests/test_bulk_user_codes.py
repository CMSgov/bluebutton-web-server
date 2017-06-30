#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from ..models import UserProfile
from ..models import UserRegisterCode
from django.core.urlresolvers import reverse


class UserRegisterCodeTestCase(TestCase):
    """
    Test Sending a code to allow users to register
    """

    def setUp(self):
        self.u = User.objects.create_user(username="fred",
                                          first_name="Fred",
                                          last_name="Flinstone",
                                          email='fred@example.com',
                                          password="foobar",)
        UserProfile.objects.create(user=self.u,
                                   user_type="DEV",
                                   create_applications=True,
                                   remaining_user_invites=2)
        self.csv_text = """id,first_name,last_name,email,username,code
                            999999999,Fred,Flinstone,fred@example.com,fred,bone
                            888888888,Willma,Flinstone,willma@example.com,willma,dog
                            """
        self.client = Client()

    def test_bulk_user_codes_form(self):
        self.client.login(username="fred", password="foobar")
        url = reverse('bulk_user_codes')
        form_data = {'csv_text': self.csv_text}
        response = self.client.post(url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'signup codes created')
        self.assertEqual(UserRegisterCode.objects.filter(sender=self.u).count(), 2)
