from collections import OrderedDict
from django.http import JsonResponse
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from oauth2_provider.decorators import protected_resource
from rest_framework.decorators import api_view, permission_classes, authentication_classes

from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.permissions import ApplicationActivePermission


def get_userinfo(user):
    """
    OIDC-style userinfo
    """
    data = OrderedDict()
    data['sub'] = user.username
    data['name'] = "%s %s" % (user.first_name, user.last_name)
    data['given_name'] = user.first_name
    data['family_name'] = user.last_name
    data['email'] = user.email
    data['iat'] = user.date_joined

    # Get the FHIR ID if its there
    fhir_id = get_fhir_id(user)
    if fhir_id:
        data['patient'] = fhir_id
        data['sub'] = fhir_id
    return data


@api_view(["GET"])
@authentication_classes([OAuth2Authentication])
@permission_classes([ApplicationActivePermission,
                     TokenHasProtectedCapability,
                     DataAccessGrantPermission])
@protected_resource()
def openidconnect_userinfo(request, **kwargs):
    return JsonResponse(get_userinfo(request.resource_owner))


def get_fhir_id(user):

    r = None
    if Crosswalk.objects.filter(user=user).exists():
        c = Crosswalk.objects.get(user=user)
        r = c.fhir_id
    return r
