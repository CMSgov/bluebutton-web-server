import logging

import json
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from apps.capabilities.constants import FHIR_PREFIX_CREATE_STARTER_SCOPES, SUPPORTED_RESOURCES
from apps.capabilities.models import ProtectedCapability

from apps.constants import HHS_SERVER_LOGNAME_FMT

logger = logging.getLogger(HHS_SERVER_LOGNAME_FMT.format(__name__))


def create_group(name="BlueButton"):

    g, created = Group.objects.get_or_create(name=name)
    if created:
        logger.info("%s group created" % (name))
    else:
        logger.info("%s group pre-existing. Create skipped." % (name))
    return g


def create_fhir_readonly_capability(group,
                                    fhir_resource_type,
                                    FHIR_PREFIX_CREATE_STARTER_SCOPES=FHIR_PREFIX_CREATE_STARTER_SCOPES,
                                    title="",
                                    description=""):
    c = None
    if not title:
        title = "My %s records." % (fhir_resource_type)

    smart_scope_string = "patient/%.read" % (fhir_resource_type)
    pr = []
    pr.append(["GET", "%s%s/" % (FHIR_PREFIX_CREATE_STARTER_SCOPES, fhir_resource_type)])
    pr.append(["GET", "%s%s/[id]" % (FHIR_PREFIX_CREATE_STARTER_SCOPES, fhir_resource_type)])

    if not ProtectedCapability.objects.filter(slug=smart_scope_string).exists():
        c = ProtectedCapability.objects.create(group=group,
                                               title=title,
                                               description=description,
                                               slug=smart_scope_string,
                                               protected_resources=json.dumps(pr, indent=4))
    return c


class Command(BaseCommand):
    help = 'Create A started set of FHIR Protected Capapabvilities with  ReadOnly permissions.'

    def handle(self, *args, **options):
        g = create_group()
        for r in SUPPORTED_RESOURCES:
            create_fhir_readonly_capability(g, r)
