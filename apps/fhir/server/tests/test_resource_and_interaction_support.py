#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: test_resource_and_interaction_support
Created: 5/19/16 1:27 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.conf import settings
import base64, json

ENCODED = settings.ENCODING


class FHIR_CheckUnAuthInteraction_TestCase(TestCase):
    """
    Test FHIR for Unauthorized Interaction
    """

    #auth_headers = {"HTTP_AUTHORIZATION": "Basic "+base64.b64encode(user_password)}
    fixtures=['provider-directory-resources.json']


    def setUp(self):
        USERNAME_FOR_TEST = "alan"
        PASSWORD_FOR_TEST = "p"
        self.credentials = "%s:%s" % (USERNAME_FOR_TEST, PASSWORD_FOR_TEST)
        self.authorization = "Basic %s" % (base64.b64encode(self.credentials.encode(ENCODED)))
        # self.credentials = base64.b64encode(self.credentials)


        self.resource_type = "Organization"
        self.client=Client()
        self.client.defaults['HTTP_AUTHORIZATION'] = self.authorization #'Basic ' + self.credentials
        #self.client.defaults['HTTP_X_REQUESTED_WITH'] ='XMLHttpRequest'

        self.url=reverse('fhir_create', args = (self.resource_type,)) + '?foo.bar'


    def test_unauth_interaction_fhir(self):
        """test_fhir_create"""
        response = self.client.get(self.url)

        # Check some response details
        self.assertEqual(response.status_code, 403)

class FHIR_CheckUnAuthResource_TestCase(TestCase):
    """
    Test FHIR for Unsupported Resource
    """

    #auth_headers = {"HTTP_AUTHORIZATION": "Basic "+base64.b64encode(user_password)}
    fixtures=['provider-directory-resources.json']


    def setUp(self):
        USERNAME_FOR_TEST = "alan"
        PASSWORD_FOR_TEST = "p"
        self.credentials = "%s:%s" % (USERNAME_FOR_TEST, PASSWORD_FOR_TEST)
        self.authorization = "Basic %s" % (base64.b64encode(self.credentials.encode(ENCODED)))
        # self.credentials = base64.b64encode(self.credentials)


        self.resource_type = "Foo"
        self.client = Client()
        self.client.defaults['HTTP_AUTHORIZATION'] = self.authorization #'Basic ' + self.credentials

        #self.client.defaults['HTTP_X_REQUESTED_WITH'] ='XMLHttpRequest'

        self.url=reverse('fhir_create', args = (self.resource_type,)) + '?foo.bar'


    def test_unauth_interaction_fhir(self):
        """test_unsupported_resource"""
        response = self.client.get(self.url)

        # Check some response details
        self.assertEqual(response.status_code, 404)

