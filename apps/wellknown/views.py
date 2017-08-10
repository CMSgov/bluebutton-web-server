from django.http import JsonResponse
from django.views.decorators.http import require_GET
from collections import OrderedDict
from django.conf import settings
from django.core.urlresolvers import reverse


@require_GET
def openid_configuration(request):
    """
    Views that returns openid_configuration.
    """
    data = OrderedDict()
    data["issuer"] = getattr(settings, 'HOSTNAME_URL', 'http://localhost:8000')
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

    return JsonResponse(data)
