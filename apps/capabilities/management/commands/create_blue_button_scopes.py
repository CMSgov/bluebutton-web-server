import json
import logging

from django.contrib.auth.models import Group
from django.urls import reverse
from django.core.management.base import BaseCommand
from apps.capabilities.constants import FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES
from apps.capabilities.models import ProtectedCapability

import apps.logging.request_logger as bb2logging

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))



def create_group(name='BlueButton'):

    g, created = Group.objects.get_or_create(name=name)
    if created:
        logger.info('%s group created' % (name))
    else:
        logger.info('%s group pre-existing. Create skipped.' % (name))
    return g


def create_userinfo_capability(group, title='Profile information including name and email.'):

    c = None
    description = 'OIDC userinfo endpoint %s' % (
        reverse('openid_connect_userinfo'))
    scope_string = 'profile'
    pr = []
    pr.append(['GET', '/v[123]/connect/userinfo.*$'])

    if not ProtectedCapability.objects.filter(slug=scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_openid_capability(group, title='Openid profile permissions.'):
    # Currently inert, but should be required with profile for profile information
    c = None
    description = 'Enables user authentication and provides a unique identifier with basic profile info.'
    scope_string = 'openid'
    pr = []

    if not ProtectedCapability.objects.filter(slug=scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_patient_capability(group, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES, title='My general patient and demographic information.'):

    c = None
    description = 'Patient FHIR Resource'
    smart_scope_string = 'patient/Patient.read'
    pr = []
    pr.append(['GET', '%sPatient[/?].*$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    pr.append(['GET', '%sPatient[/]?$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_patient_read_capability(group, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES, title='Read my general patient and demographic information.'):

    c = None
    description = 'Patient FHIR Resource'
    smart_scope_string = 'patient/Patient.r'
    pr = []
    # Backward compatible with .read. In the future, we may limit this to Patient/id urls
    pr.append(['GET', '%sPatient[/?].*$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_patient_search_capability(group,
                                     FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES,
                                     title='Search my general patient and demographic information.'):

    c = None
    description = 'Patient FHIR Resource'
    smart_scope_string = 'patient/Patient.s'
    pr = []
    pr.append(['GET', '%sPatient[/]?$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_patient_read_search_capability(group,
                                          FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES,
                                          title='Read and search my general patient and demographic information.'):

    c = None
    description = 'Patient FHIR Resource'
    smart_scope_string = 'patient/Patient.rs'
    pr = []
    # Functionally the same as .r for backwards compatibility
    pr.append(['GET', '%sPatient[/?].*$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    pr.append(['GET', '%sPatient[/]?$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_eob_capability(group, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES, title='My Medicare claim information.'):
    c = None
    description = 'ExplanationOfBenefit FHIR Resource'
    smart_scope_string = 'patient/ExplanationOfBenefit.read'
    pr = []
    pr.append(['GET', '%sExplanationOfBenefit[/?].*$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    pr.append(['GET', '%sExplanationOfBenefit[/]?$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_eob_read_capability(group, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES, title='Read my Medicare claim information.'):
    c = None
    description = 'ExplanationOfBenefit FHIR Resource'
    smart_scope_string = 'patient/ExplanationOfBenefit.r'
    pr = []
    # Backward compatible with .read. In the future, we may limit this to ExplanationOfBenefit/id urls
    pr.append(['GET', '%sExplanationOfBenefit[/?].*$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_eob_search_capability(group, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES, title='Search my Medicare claim information.'):
    c = None
    description = 'ExplanationOfBenefit FHIR Resource'
    smart_scope_string = 'patient/ExplanationOfBenefit.s'
    pr = []
    pr.append(['GET', '%sExplanationOfBenefit[/]?$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_eob_read_search_capability(group, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES, title='Read and search my Medicare claim information.'):

    c = None
    description = 'ExplanationOfBenefit FHIR Resource'
    smart_scope_string = 'patient/ExplanationOfBenefit.rs'
    pr = []
    # Functionally the same as .r for backwards compatibility
    pr.append(['GET', '%sExplanationOfBenefit[/?].*$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    pr.append(['GET', '%sExplanationOfBenefit[/]?$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_coverage_capability(group, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES, title='My Medicare and supplemental coverage information.'):
    c = None
    description = 'Coverage FHIR Resource'
    smart_scope_string = 'patient/Coverage.read'
    pr = []
    pr.append(['GET', '%sCoverage[/?].*$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    pr.append(['GET', '%sCoverage[/]?$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_coverage_read_capability(group,
                                    FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES,
                                    title='Read my Medicare and supplemental coverage information.'):
    c = None
    description = 'Coverage FHIR Resource'
    smart_scope_string = 'patient/Coverage.r'
    pr = []
    # Backward compatible with .read. In the future, we may limit this to Coverage/id urls
    pr.append(['GET', '%sCoverage[/?].*$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_coverage_search_capability(group,
                                      FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES,
                                      title='Search my Medicare and supplemental coverage information.'):
    c = None
    description = 'Coverage FHIR Resource'
    smart_scope_string = 'patient/Coverage.s'
    pr = []
    # Backward compatible with .read. In the future, we may limit this to Coverage/id urls
    pr.append(['GET', '%sCoverage[/]?$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_coverage_read_search_capability(group,
                                           FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES,
                                           title='Read and search my Medicare and supplemental coverage information.'):
    c = None
    description = 'Coverage FHIR Resource'
    smart_scope_string = 'patient/Coverage.rs'
    pr = []
    # Backward compatible with .read. In the future, we may limit this to Coverage/id urls
    pr.append(['GET', '%sCoverage[/?].*$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    pr.append(['GET', '%sCoverage[/]?$' % FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES])
    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_launch_capability(group, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES, title='Patient launch context.'):

    c = None
    description = 'Launch with FHIR Patient context.'
    smart_scope_string = 'launch/patient'
    pr = []

    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               default=True,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


def create_token_management_capability(group):

    c = None
    description = 'Allow an app to manage all of a user\'s tokens.'
    slug = 'token_management'
    title = 'Token Management'
    protected_resources = []
    protected_resources.append(['GET\', \'/some-url'])

    if not ProtectedCapability.objects.filter(slug=slug).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=slug,
                                               default=False,
                                               protected_resources=json.dumps(protected_resources, indent=4))
    return c


def create_token_introspect_capability(group):

    c = None
    description = 'Allow an app to introspect a user\'s tokens.'
    slug = 'token_introspect'
    title = 'Token Introspect'
    protected_resources = []
    protected_resources.append(['POST\', \'/v[123]/o/introspect'])

    if not ProtectedCapability.objects.filter(slug=slug).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=slug,
                                               default=False,
                                               protected_resources=json.dumps(protected_resources, indent=4))
    return c


class Command(BaseCommand):
    help = 'Create BlueButton Group and Scopes'

    def handle(self, *args, **options):
        g = create_group()
        create_userinfo_capability(g)
        create_patient_capability(g, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES)
        create_eob_capability(g, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES)
        create_coverage_capability(g, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES)
        create_patient_read_capability(g, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES)
        create_patient_search_capability(g, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES)
        create_patient_read_search_capability(g, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES)
        create_eob_read_capability(g, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES)
        create_eob_search_capability(g, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES)
        create_eob_read_search_capability(g, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES)
        create_coverage_read_capability(g, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES)
        create_coverage_search_capability(g, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES)
        create_coverage_read_search_capability(g, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES)
        create_launch_capability(g, FHIR_PREFIX_CREATE_BLUE_BUTTON_SCOPES)
        create_openid_capability(g)
        create_token_management_capability(g)
        create_token_introspect_capability(g)
