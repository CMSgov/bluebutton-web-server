import json
from django.contrib.auth.models import Group
from django.urls import reverse
from django.core.management.base import BaseCommand
from ...models import ProtectedCapability

import logging

logger = logging.getLogger('hhs_server.%s' % __name__)
fhir_prefix = "/v1/fhir/"


def create_group(name="BlueButton"):

    g, created = Group.objects.get_or_create(name=name)
    if created:
        logger.info("%s group created" % (name))
    else:
        logger.info("%s group pre-existing. Create skipped." % (name))
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
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
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
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
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
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


class Command(BaseCommand):
    help = 'Create BlueButton Group and Scopes'

    def handle(self, *args, **options):
        g = create_group()
        create_userinfo_capability(g)
        create_patient_capability(g, fhir_prefix)
        create_eob_capability(g, fhir_prefix)
        create_coverage_capability(g, fhir_prefix)
