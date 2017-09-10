import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from collections import OrderedDict
from django.conf import settings
from django.core.urlresolvers import reverse

logger = logging.getLogger('hhs_server.%s' % __name__)


@require_GET
def openid_configuration(request):
    """
    Views that returns openid_configuration.
    """
    data = OrderedDict()
    data["issuer"] = getattr(settings, 'HOSTNAME_URL', 'http://localhost:8000')

    if "http://" in data["issuer"].lower():
        pass
    elif "https://" in data["issue"].lower():
        pass
    else:
        logger.debug("HOSTNAME_URL [%s] "
                     "does not contain http prefix. "
                     "data[issuer]:%s" % (settings.HOSTNAME_URL, data['issuer']))
        # no http/https prefix in HOST_NAME_URL so we add it
        if request.is_secure():
            http_mode = 'https://'
        else:
            http_mode = 'http://'

        # prefix hostname with http/https://
        data["issuer"] = http_mode + data["issuer"]

    data["authorization_endpoint"] = data['issuer'] + \
        reverse('oauth2_provider:authorize')
    data["token_endpoint"] = data['issuer'] + reverse('oauth2_provider:token')
    data["userinfo_endpoint"] = data['issuer'] + \
        reverse('openid_connect_userinfo')
    data["ui_locales_supported"] = ["en-US", ]
    # data["service_documentation"] = getattr(settings, 'DEVELOPER_DOCS', "")
    data["grant_types_supported"] = ["implicit", "authorization_code", "refresh_token",
                                     "password", "client_credentials"]
    if settings.DCRP:
        data["registration_endpoint"] = data[
            "issuer"] + reverse('dcrp_register')

    print(".well-known data:%s" % data)

    return JsonResponse(data)
