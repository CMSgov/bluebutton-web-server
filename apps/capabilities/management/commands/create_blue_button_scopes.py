import json
import logging

from django.contrib.auth.models import Group
from django.urls import reverse
from django.core.management.base import BaseCommand
from django.core.management import call_command
from ...models import ProtectedCapability

import apps.logging.request_logger as bb2logging

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))

fhir_prefix = "/v1/fhir/"


def create_group(name="BlueButton"):

    g, created = Group.objects.get_or_create(name=name)
    if created:
        logger.info("%s group created" % (name))
    else:
        logger.info("%s group pre-existing. Create skipped." % (name))
    return g


def create_userinfo_capability(group, title="Profile information including name and email."):

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


def create_openid_capability(group, title="Openid profile permissions."):
    # Currently inert, but should be required with profile for profile information
    c = None
    description = "OIDC userinfo endpoint %s" % (
        reverse('openid_connect_userinfo'))
    scope_string = "openid"
    pr = []

    if not ProtectedCapability.objects.filter(slug=scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_patient_capability(group, fhir_prefix, title="My general patient and demographic information."):

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


def create_patient_read_capability(group, fhir_prefix, title="Read my general patient and demographic information."):

    c = None
    description = "Patient FHIR Resource"
    smart_scope_string = "patient/Patient.r"
    pr = []
    # Backward compatible with .read. In the future, we may limit this to Patient/id urls
    pr.append(["GET", "%sPatient/" % fhir_prefix])
    pr.append(["GET", "%sPatient/[id]" % fhir_prefix])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_patient_search_capability(group,
                                     fhir_prefix,
                                     title="Search my general patient and demographic information."):

    c = None
    description = "Patient FHIR Resource"
    smart_scope_string = "patient/Patient.s"
    pr = []
    pr.append(["GET", "%sPatient/" % fhir_prefix])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_patient_read_search_capability(group,
                                          fhir_prefix,
                                          title="Read and search my general patient and demographic information."):

    c = None
    description = "Patient FHIR Resource"
    smart_scope_string = "patient/Patient.rs"
    pr = []
    # Functionally the same as .r for backwards compatibility
    pr.append(["GET", "%sPatient/" % fhir_prefix])
    pr.append(["GET", "%sPatient/[id]" % fhir_prefix])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_eob_capability(group, fhir_prefix, title="My Medicare claim information."):
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

def create_eob_read_capability(group, fhir_prefix, title="Read my Medicare claim information."):
    c = None
    description = "ExplanationOfBenefit FHIR Resource"
    smart_scope_string = "patient/ExplanationOfBenefit.r"
    pr = []
    # Backward compatible with .read. In the future, we may limit this to ExplinationOfBenefit/id urls
    pr.append(["GET", "%sExplanationOfBenefit/" % fhir_prefix])
    pr.append(["GET", "%sExplanationOfBenefit/[id]" % fhir_prefix])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c

def create_eob_search_capability(group, fhir_prefix, title="Search my Medicare claim information."):
    c = None
    description = "ExplanationOfBenefit FHIR Resource"
    smart_scope_string = "patient/ExplanationOfBenefit.s"
    pr = []
    pr.append(["GET", "%sExplanationOfBenefit/" % fhir_prefix])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c

def create_eob_read_search_capability(group, fhir_prefix, title="Read and search my Medicare claim information."):

    c = None
    description = "Patient FHIR Resource"
    smart_scope_string = "patient/Patient.rs"
    pr = []
    # Functionally the same as .r for backwards compatibility
    pr.append(["GET", "%sPatient/" % fhir_prefix])
    pr.append(["GET", "%sPatient/[id]" % fhir_prefix])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_coverage_capability(group, fhir_prefix, title="My Medicare and supplemental coverage information."):
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

def create_coverage_read_capability(group,
                                    fhir_prefix,
                                    title="Read my Medicare and supplemental coverage information."):
    c = None
    description = "Coverage FHIR Resource"
    smart_scope_string = "patient/Coverage.r"
    pr = []
    # Backward compatible with .read. In the future, we may limit this to Coverage/id urls
    pr.append(["GET", "%sCoverage/" % fhir_prefix])
    pr.append(["GET", "%sCoverage/[id]" % fhir_prefix])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c

def create_coverage_search_capability(group,
                                      fhir_prefix,
                                      title="Search my Medicare and supplemental coverage information."):
    c = None
    description = "Coverage FHIR Resource"
    smart_scope_string = "patient/Coverage.s"
    pr = []
    # Backward compatible with .read. In the future, we may limit this to Coverage/id urls
    pr.append(["GET", "%sCoverage/" % fhir_prefix])
    pr.append(["GET", "%sCoverage/[id]" % fhir_prefix])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c

def create_coverage_read_search_capability(group,
                                           fhir_prefix,
                                           title="Read and search my Medicare and supplemental coverage information."):
    c = None
    description = "Coverage FHIR Resource"
    smart_scope_string = "patient/Coverage.r"
    pr = []
    # Backward compatible with .read. In the future, we may limit this to Coverage/id urls
    pr.append(["GET", "%sCoverage/" % fhir_prefix])
    pr.append(["GET", "%sCoverage/[id]" % fhir_prefix])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_launch_capability(group, fhir_prefix, title="Patient launch context."):

    c = None
    description = "Launch with FHIR Patient context."
    smart_scope_string = "launch/patient"
    pr = []

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
        create_patient_read_capability(g, fhir_prefix)
        create_patient_search_capability(g, fhir_prefix)
        create_patient_read_search_capability(g, fhir_prefix)
        create_eob_read_capability(g, fhir_prefix)
        create_eob_search_capability(g, fhir_prefix)
        create_eob_read_search_capability(g, fhir_prefix)
        create_coverage_read_capability(g, fhir_prefix)
        create_coverage_read_search_capability(g, fhir_prefix)
        create_launch_capability(g, fhir_prefix)
        create_openid_capability(g)

        call_command('loaddata', 'internal_application_labels.json')

