import logging
import subprocess

from django.db import connection
from waffle import switch_is_active

import apps.logging.request_logger as bb2logging

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))


def django_rds_database():
    connection.ensure_connection()
    return connection.is_usable()


def splunk_services():
    if switch_is_active('splunk_monitor'):
        pl = subprocess.Popen(['ps', '-ef'], stdout=subprocess.PIPE).communicate()[0]
        if "splunkd" in str(pl):
            return True
        return False
    return True


internal_services = (
    django_rds_database,
    splunk_services,
)
