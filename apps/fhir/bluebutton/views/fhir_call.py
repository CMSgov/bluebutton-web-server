#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server/apps/fhir/bluebutton/views
FILE: fhir_call
Created: 2/24/17 12:36 AM

File created by: '@ekivemark'

Creating a class object to handle requests

"""
import os

from django.conf import settings
from ..models import FhirServer

class FHIRRequest:
    """ Handle data to and from requests with Backend FHIR Server """

    certstore_path = settings.FHIR_CLIENT_CERTSTORE

    def __init__(self):
        # Client Authentication defaults to false
        self.clientauth = False

    def set_clientauth(self, auth_status=False):
        self.clientauth = auth_status

        if not self.clientauth:
            self.cert = ()

    def set_clientcert(self, cert_file_path, cert_key_path):
        self.cert = (cert_file_path, cert_key_path)

    def print_settings(self):
        print("clientauth: %s" % self.clientauth)
        print("certificate: %s" % self.cert)

