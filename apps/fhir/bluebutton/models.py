#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: models
Created: 5/19/16 12:27 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

import json

# Create your models here.

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from apps.fhir.server.models import SupportedResourceType


@python_2_unicode_compatible
class ResourceTypeControl(models.Model):
    resource_name = models.ForeignKey(SupportedResourceType)
    override_url_id = models.BooleanField(help_text="Does this resource need "
                                                    "to mask the id in the "
                                                    "url?")
    override_search = models.BooleanField(help_text="Do search parameters need "
                                                    "to be filtered to avoid "
                                                    "revealing other people's "
                                                    "data?")
    search_block = models.TextField(max_length=5120,
                                    blank=True,
                                    default="",
                                    help_text="list of values that need to be "
                                              "removed from search parameters. "
                                              "eg. <b>Patient</b>")
    search_add = models.TextField(max_length=200,
                                  blank=True,
                                  default="",
                                  help_text="list of keys that need to be "
                                            "added to search parameters to "
                                            "filter information that is "
                                            "returned. eg. "
                                            "<b>Patient=%PATIENT%</b>")
    group_allow = models.TextField(max_length=100,
                                   blank=True,
                                   default="",
                                   help_text="groups permitted to access "
                                             "resource.")
    group_exclude = models.TextField(max_length=100,
                                     blank=True,
                                     default="",
                                     help_text="groups blocked from accessing "
                                               "resource.")
    default_url = models.URLField(blank=True,
                                  verbose_name="Default FHIR URL with "
                                               "terminating /",
                                  help_text="Exclude the resource. eg. "
                                            "<b>https://fhirserver.com/fhir/"
                                            "Patient/</b> is entered as "
                                            "<b>https://fhirserver.com/fhir/"
                                            "</b></br>Leave blank to accept "
                                            "system default.")
    # Add default_url unless the resource is defined via crosswalk

    # Python2 uses __unicode__(self):
    def __str__(self):
        return self.resource_name.resource_name

    def set_search_block(self, x):
        self.search_block = json.dumps(x)

    def get_search_block(self):
        if self.search_block == "":
            search_list = []
        else:
            search_list = self.search_block
        return json.loads(search_list)

    def set_search_add(self, x):
        self.search_add = json.dumps(x)

    def get_search_add(self):
        if self.search_add == "":
            search_list = []
        else:
            search_list = self.search_add
        return json.loads(search_list)

    def replace_url_id(self):
        return self.override_url_id

    def set_group_allow(self, x):
        self.group_allow = json.dumps(x)

    def get_group_allow(self):
        if self.group_allow == "":
            group_list = []
        else:
            group_list = self.group_allow
        return json.loads(group_list)

    def set_group_exclude(self, x):
        self.group_exclude = json.dumps(x)

    def get_group_exclude(self):
        if self.group_exclude == "":
            group_list = []
        else:
            group_list = self.group_exclude
        return json.loads(group_list)


@python_2_unicode_compatible
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
    fhir_url = models.URLField(verbose_name="Full URL to FHIR API with "
                                            "terminating /")
    shard_by = models.CharField(max_length=80,
                                default="Patient",
                                verbose_name="Key Resource type")

    def __str__(self):
        return self.name


@python_2_unicode_compatible
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


    def get_fhir_resource_url(self, resource_type):
        # Return the fhir server url

        full_url = self.fhir_source.fhir_url
        if full_url.endswith("/"):
            pass
        else:
            full_url += "/"

        if resource_type:
            full_url += resource_type + "/"

        return full_url
