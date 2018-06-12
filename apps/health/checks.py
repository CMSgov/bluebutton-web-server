import requests
import logging
from django.db import connection
from apps.fhir.bluebutton.utils import get_resourcerouter
from apps.fhir.server import connection as backend_connection

logger = logging.getLogger('hhs_server.%s' % __name__)


def databases():
    connection.ensure_connection()
    return connection.is_usable()


def dataserver():
        resource_router = get_resourcerouter()
        target_url = resource_router.fhir_url + "metadata"
        r = requests.get(target_url,
                         params={"_format": "json"},
                         cert=backend_connection.certs(),
                         verify=False)
        try:
            r.raise_for_status()
        except Exception:
            logger.exception("Failed to ping backend")
            return False
        return r.json()


services = (
    databases,
    dataserver,
)
