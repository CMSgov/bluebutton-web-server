import logging
import requests
import subprocess

from django.db import connection
from waffle import switch_is_active

from apps.fhir.server.settings import fhir_settings
from apps.fhir.bluebutton.utils import FhirServerAuth
from apps.mymedicare_cb.authorization import OAuth2ConfigSLSx

import apps.logging.request_logger as bb2logging

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))


def django_rds_database(v2=False):
    connection.ensure_connection()
    return connection.is_usable()


def splunk_services(v2=False):
    if switch_is_active('splunk_monitor'):
        pl = subprocess.Popen(['ps', '-ef'], stdout=subprocess.PIPE).communicate()[0]
        if "splunkd" in str(pl):
            return True
        return False
    return True


def bfd_fhir_dataserver(v2=False):
    fhir_server_auth = FhirServerAuth()

    target_url = "{}{}".format(fhir_settings.fhir_url, "/v2/fhir/metadata" if v2 else "/v1/fhir/metadata")
    r = requests.get(target_url,
                     params={"_format": "json"},
                     cert=(fhir_server_auth['cert_file'], fhir_server_auth['key_file']),
                     verify=False,
                     timeout=5)
    try:
        r.raise_for_status()
    except Exception:
        logger.exception("Failed to ping backend")
        return False
    return r.json()


def slsx(v2=False):
    # Perform health check on SLSx service
    slsx_client = OAuth2ConfigSLSx()
    return slsx_client.service_health_check(None)


internal_services = (
    django_rds_database,
    splunk_services,
)

external_services = (
    bfd_fhir_dataserver,
    slsx,
)

slsx_services = (
    slsx,
)

bfd_services = (
    bfd_fhir_dataserver,
)

db_services = (
    django_rds_database,
)
