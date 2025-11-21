from collections import OrderedDict
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from oauth2_provider.decorators import protected_resource
from oauth2_provider.models import get_access_token_model, get_application_model
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from waffle import get_waffle_flag_model

from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.permissions import ApplicationActivePermission

from apps.versions import Versions


def _get_userinfo(user, version=Versions.NOT_AN_API_VERSION):
    """ OIDC-style userinfo

    Args:
        user (AccessToken): AccessToken object from database
        version (int): the version of BFD being accessed

    Returns:
        data (dict): dictionary of values according to OIDC
    """
    data = OrderedDict()
    data['sub'] = user.username
    data['name'] = "%s %s" % (user.first_name, user.last_name)
    data['given_name'] = user.first_name
    data['family_name'] = user.last_name
    data['email'] = user.email
    data['iat'] = user.date_joined

    fhir_id = get_fhir_id(user, version)
    if fhir_id:
        data['patient'] = fhir_id
        data['sub'] = fhir_id
    return data


@api_view(["GET"])
@authentication_classes([OAuth2Authentication])
@permission_classes([ApplicationActivePermission,
                     TokenHasProtectedCapability,
                     DataAccessGrantPermission])
@protected_resource()  # Django OAuth Toolkit -> resource_owner = AccessToken
def _openidconnect_userinfo(request, version=Versions.NOT_AN_API_VERSION):
    # NOTE: The **kwargs are not used anywhere down the callchain, and are being ignored.
    # 4250: Handling to ensure this only returns successfully if the flag is enabled for the application
    # associated with the user making the call
    if version == Versions.V3:
        user = get_user_model().objects.get(username=request.resource_owner)
        access_token = get_access_token_model().objects.get(user_id=user.id)
        application = get_application_model().objects.get(id=access_token.application_id)
        application_user = get_user_model().objects.get(id=application.user_id)
        flag = get_waffle_flag_model().get('v3_early_adopter')
        if flag.id is None or not flag.is_active_for_user(application_user):
            return JsonResponse(
                {'status_code': 403, 'message': settings.APPLICATION_DOES_NOT_HAVE_V3_ENABLED_YET.format(application.name)},
                status=403,
            )

    return JsonResponse(_get_userinfo(request.resource_owner, version))


def openidconnect_userinfo_v1(request):
    return _openidconnect_userinfo(request, version=Versions.V1)


def openidconnect_userinfo_v2(request):
    return _openidconnect_userinfo(request, version=Versions.V2)


def openidconnect_userinfo_v3(request):
    print("openidconnect_userinfo_v3 request: ", request.__dict__)
    print("openidconnect_userinfo_v3 user: ", request.user.__dict__)
    return _openidconnect_userinfo(request, version=Versions.V3)


def get_fhir_id(user, version=Versions.NOT_AN_API_VERSION):
    r = None
    if Crosswalk.objects.filter(user=user).exists():
        c = Crosswalk.objects.get(user=user)
        # fhir_id expects an integer (1, 2, 3, etc.)
        r = c.fhir_id(Versions.as_int(version))
    return r
