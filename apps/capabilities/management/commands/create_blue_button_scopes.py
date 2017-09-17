from __future__ import absolute_import
from __future__ import unicode_literals
import json
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.core.management.base import BaseCommand
from ...models import ProtectedCapability

__author__ = "Alan Viars"


fhir_prefix = "/protected/bluebutton/fhir/v1/"


def create_group(name="BlueButton"):

    g, created = Group.objects.get_or_create(name=name)
    if created:
        print("%s group created" % (name))
    else:
        print("%s group pre-existing. Create skipped." % (name))
    return g


def create_userinfo_capability(group,
                               title="Profile information including name and email."):

    c = None
    description = "OIDC userinfo endpoint %s" % (
        reverse('openid_connect_userinfo'))
    scope_string = "profile"
    pr = []
    pr.append(["GET", reverse('openid_connect_userinfo')])

    if not ProtectedCapability.objects.filter(slug=scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
        print("%s - %s created." % (c.slug, c.title))
    return c


def create_patient_capability(group,
                              fhir_prefix,
                              title="My general patient and demographic information."):

    c = None
    description = "Patient FHIR Resource"
    smart_scope_string = "patient/Patient.read"
    pr = []
    pr.append(["GET", "%sPatient/" % fhir_prefix])
    pr.append(["GET", "%sPatient/[id]" % fhir_prefix])
    pr.append(["GET", "%sPatient/[id]/_history" % fhir_prefix])
    pr.append(["GET", "%sPatient/[id]/_history/[vid]" % fhir_prefix])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
        print("%s - %s created" % (c.slug, c.title))
    return c


def create_eob_capability(group,
                          fhir_prefix,
                          title="My Medicare claim information."):
    c = None
    description = "ExplanationOfBenefit FHIR Resource"
    smart_scope_string = "patient/ExplanationOfBenefit.read"
    pr = []
    pr.append(["GET", "%sExplanationOfBenefit/" % fhir_prefix])
    pr.append(["GET", "%sExplanationOfBenefit/[id]" % fhir_prefix])
    pr.append(["GET", "%sExplanationOfBenefit/[id]/_history" % fhir_prefix])
    pr.append(["GET", "%sExplanationOfBenefit/[id]/_history/[vid]" % fhir_prefix])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
        print("%s - %s created." % (c.slug, c.title))
    return c


def create_coverage_capability(group,
                               fhir_prefix,
                               title="My Medicare and supplemental coverage information."):
    c = None
    description = "Coverage FHIR Resource"
    smart_scope_string = "patient/Coverage.read"
    pr = []
    pr.append(["GET", "%sCoverage/" % fhir_prefix])
    pr.append(["GET", "%sCoverage/[id]" % fhir_prefix])
    pr.append(["GET", "%sCoverage/[id]/_history" % fhir_prefix])
    pr.append(["GET", "%sCoverage/[id]/_history/[vid]" % fhir_prefix])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
        print("%s - %s created." % (c.slug, c.title))
    return c


class Command(BaseCommand):
    help = 'Create BlueButton Group and Scopes'

    def handle(self, *args, **options):
        g = create_group()
        # Delete any pre-existing BlueButton Scopes
        # print("Deleting pre-existing scope in the BlueButton group.")
        # ProtectedCapability.objects.filter(group=g).delete()
        #
        create_userinfo_capability(g)
        create_patient_capability(g, fhir_prefix)
        create_eob_capability(g, fhir_prefix)
        create_coverage_capability(g, fhir_prefix)
        print("Done. Stay classy, San Diego.")
