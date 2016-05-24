from __future__ import unicode_literals
from __future__ import absolute_import

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: apps.fhir.bluebutton.test_models
Created: 5/19/16 12:31 PM

Test models

"""
__author__ = 'Mark Scrimshire:@ekivemark'


import logging

from ..models import FhirServer, Crosswalk
from apps.test import BaseApiTest

logger = logging.getLogger('tests.%s' % __name__)


class TestModels(BaseApiTest):
    def test_get_full_url_good(self):
        # Create a user
        user = self._create_user('john', 'password', first_name='John',
                                   last_name='Smith',
                                   email='john@smith.net', )
        # created a default user
        logger.debug("user: '%s'", user)

        fs = FhirServer.objects.create(name="Main Server",
                                       fhir_url="http://localhost:8000/fhir/",
                                       shard_by="Patient")

        cw = Crosswalk.objects.create(user=user,
                                      fhir_source=fs,
                                      fhir_id="123456")

        fhir = Crosswalk.objects.get(user=user.pk)

        url_info = fhir.get_fhir_patient_url()

        expected_result = fs.fhir_url+fs.shard_by+"/"+cw.fhir_id

        logger.debug("test for equality: %s = %s", url_info, expected_result )

        self.assertEqual(url_info, expected_result)


    def test_get_full_url_bad(self):

        # Create a user
        user = self._create_user('john', 'password', first_name='John',
                                 last_name='Smith',
                                 email='john@smith.net', )

        # created a default user
        logger.debug("user: '%s'", user)

        fs = FhirServer.objects.create(name="Main Server",
                                       fhir_url="http://localhost:8000/fhir/",
                                       shard_by="Patient")

        cw = Crosswalk.objects.create(user=user,
                                      fhir_source=fs,
                                      fhir_id="123456")

        fhir = Crosswalk.objects.get(user=user.pk)

        url_info = fhir.get_fhir_patient_url()

        invalid_match = "http://localhost:8000/fhir/" + "Practitioner/123456"

        logger.debug("test for inequality: %s != %s", url_info, invalid_match )

        self.assertNotEqual(url_info, invalid_match)

