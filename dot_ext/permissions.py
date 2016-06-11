from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from apps.capabilities.models import ProtectedCapability


logger = logging.getLogger('hhs_server.%s' % __name__)


# a set of messages used by the logger
_messages = {
    "resource_allowed": "token: access to resource '%s %s' allowed",
    "resource_forbidden": "token: access to resource '%s %s' forbidden",
}


def allow_resource(token, method, path):
    """
    Return True when this token has capability to allow
    request to `path` with method `method`.
    """
    logger.debug("token: checking access to resource '%s %s' is allowed",
                 method, path)

    scopes = token.scope.split()
    capabilities = ProtectedCapability.objects.filter(slug__in=scopes)
    for capability in capabilities:
        logger.debug("token: checking access with capability '%s'",
                     capability.protected_resources)
        if capability.allow(method, path):
            logger.info(_messages['resource_allowed'], method, path)
            return True

    logger.info(_messages['resource_forbidden'], method, path)
    return False
