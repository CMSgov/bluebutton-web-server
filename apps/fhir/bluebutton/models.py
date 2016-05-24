#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: models
Created: 5/19/16 12:27 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

from django.db import models

# Create your models here.

from django.conf import settings
from django.db import models


class FhirServer(models.Model):
    """
    Server URL at Profile level
    eg.
    https://fhir-server1.bluebutton.cms.gov/fhir/baseDstu2/
    https://fhir-server2.bluebutton.cms.gov/fhir/stu3/

    ID will be used as reference in CrossWalk

    """

    name = models.CharField(max_length=254,
                            verbose_name="Friendly Server Name")
    fhir_url = models.URLField(verbose_name="Full URL to FHIR API with terminating /")
    shard_by = models.CharField(max_length=80,
                                default="Patient",
                                verbose_name="Key Resource type")

    def __str__(self):
        return self.name


class Crosswalk(models.Model):
    """

    HICN/BeneID to User to FHIR Source Crosswalk and back.
    Linked to User Account
    Use fhir_url_id for id
    use fhir for resource.identifier

    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    fhir_source = models.ForeignKey(FhirServer)
    fhir_id = models.CharField(max_length=80, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    # fhir_id = Identifier used in the patient Profile URL
    # eg. /baseDstu2/Patient/{fhir_id}
    # This will allow us to construct a URL to make a call directly to
    # a record, rather than requiring a search
    # when combined with fhir_source
    # eg. https://fhir-server1.bluebutton.cms.gov/fhir/baseDstu2/ + Patient/{fhir_id}


    def __str__(self):
        return "%s %s" % (self.user.first_name,
                          self.user.last_name,
                         )


    def get_fhir_patient_url(self):
        # Return the fhir server url and {Resource_name}/{id}

        full_url = self.fhir_source.fhir_url
        if full_url.endswith("/"):
            pass
        else:
            full_url += "/"
        if self.fhir_source.shard_by:
            full_url += self.fhir_source.shard_by + "/"

        full_url += self.fhir_id

        return full_url


    def get_fhir_resource_url(self, resource):
        # Return the fhir server url

        full_url = self.fhir_source.fhir_url
        if full_url.endswith("/"):
            pass
        else:
            full_url += "/"

        return full_url
