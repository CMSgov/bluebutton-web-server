import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from collections import OrderedDict
from django.conf import settings
from django.urls import reverse

import apps.logging.request_logger as bb2logging

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))
SCOPES_SUPPORTED = [
    "openid",
    "profile",
    "launch/patient",
    "patient/Patient.read",
    "patient/ExplanationOfBenefit.read",
    "patient/Coverage.read",
    "patient/Patient.rs",
    "patient/ExplanationOfBenefit.rs",
    "patient/Coverage.rs",
]
CODE_CHALLENGE_METHODS_SUPPORTED = ["S256"]
CAPABILITIES = [
    "client-confidential-symmetric",
    "context-standalone-patient",
    "launch-standalone",
    "permission-offline",
    "permission-patient",
    "permission-v1",
    "permission-v2",
    "authorize-post"
]


@require_GET
def openid_configuration(request):
    """
    Views that returns openid_configuration.
    """
    data = OrderedDict()
    issuer = base_issuer(request)
    data = build_endpoint_info(data, issuer=issuer)
    return JsonResponse(data)


@require_GET
def smart_configuration(request):
    """
    Views that returns smart_configuration.
    """
    data = OrderedDict()
    issuer = base_issuer(request)
    data = build_smart_config_endpoint(data, issuer=issuer)
    return JsonResponse(data)


@require_GET
def smart_configuration_v3(request):
    """
    Views that returns smart_configuration for v3.
    """
    data = OrderedDict()
    issuer = base_issuer(request)
    data = build_smart_config_endpoint(data, issuer=issuer)
    
    # v3 specific info, very important since tokens aren't compatible between versions 1/2 and 3
    data["authorization_endpoint"] = data["authorization_endpoint"].replace("/v2/o/", "/v3/o/")
    data["revocation_endpoint"] = data["revocation_endpoint"].replace("/v2/o/", "/v3/o/")
    data["token_endpoint"] = data["token_endpoint"].replace("/v2/o/", "/v3/o/")
    data["fhir_metadata_uri"] = data["fhir_metadata_uri"].replace("/v2/fhir/", "/v3/fhir/")
    
    return JsonResponse(data)


def base_issuer(request):
    """
    define the base url for issuer

    """
    issuer = getattr(settings, 'HOSTNAME_URL', 'http://localhost:8000')

    if "http://" in issuer.lower():
        pass
    elif "https://" in issuer.lower():
        pass
    else:
        logger.debug("HOSTNAME_URL [%s] "
                     "does not contain http or https prefix. "
                     "Issuer:%s" % (settings.HOSTNAME_URL, issuer))
        # no http/https prefix in HOST_NAME_URL so we add it
        if request.is_secure():
            http_mode = 'https://'
        else:
            http_mode = 'http://'

        # prefix hostname with http/https://
        issuer = http_mode + issuer

    return issuer


def build_endpoint_info(data=OrderedDict(), issuer=""):
    """
    construct the data package
    issuer should be http: or https:// prefixed url.

    :param data:
    :return:
    """
    data["issuer"] = issuer
    data["authorization_endpoint"] = issuer + \
        reverse('oauth2_provider_v2:authorize-v2')
    data["revocation_endpoint"] = issuer + reverse('oauth2_provider_v2:revoke-token-v2')
    data["token_endpoint"] = issuer + \
        reverse('oauth2_provider_v2:token-v2')
    data["userinfo_endpoint"] = issuer + \
        reverse('openid_connect_userinfo_v2')
    data["ui_locales_supported"] = ["en-US", ]
    data["service_documentation"] = getattr(settings,
                                            'DEVELOPER_DOCS_URI',
                                            "https://cmsgov.github.io/bluebutton-developer-help/")
    data["op_tos_uri"] = settings.TOS_URI
    data["grant_types_supported"] = []

    for i in settings.GRANT_TYPES:
        data["grant_types_supported"].append(i[0])

    data["grant_types_supported"].append("refresh_token")

    add_authorization_code_grant(data)

    data["grant_types_supported"].remove("implicit")

    data["response_types_supported"] = ["code", "token"]
    data["fhir_metadata_uri"] = issuer + \
        reverse('fhir_conformance_metadata_v2')
    return data

def add_authorization_code_grant(data):
    if "authorization_code" not in data["grant_types_supported"]:
        data["grant_types_supported"].append("authorization_code")

    if "authorization-code" in data["grant_types_supported"]:
        data["grant_types_supported"].remove("authorization-code")


def build_smart_config_endpoint(data=OrderedDict(), issuer=""):
    """
    construct the smart config endpoint response. Takes in output of build_endpoint_info since they share many fields
    issuer should be http: or https:// prefixed url.

    :param data:
    :return:
    """

    data = build_endpoint_info(data, issuer=issuer)
    del (data["issuer"])
    del (data["userinfo_endpoint"])
    del (data["ui_locales_supported"])
    del (data["service_documentation"])
    del (data["op_tos_uri"])
    del (data["fhir_metadata_uri"])

    add_authorization_code_grant(data)

    data["grant_types_supported"].remove("refresh_token")
    data["scopes_supported"] = SCOPES_SUPPORTED
    data["code_challenge_methods_supported"] = CODE_CHALLENGE_METHODS_SUPPORTED
    data["capabilities"] = CAPABILITIES

    return data
