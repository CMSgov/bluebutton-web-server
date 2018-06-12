from django.http import JsonResponse
from django.views.decorators.http import require_GET
from apps.fhir.bluebutton.models import Crosswalk
from oauth2_provider.decorators import protected_resource
from collections import OrderedDict


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


@require_GET
@protected_resource()
def openidconnect_userinfo(request):
    user = request.resource_owner
    data = get_userinfo(user)
    return JsonResponse(data)


def get_fhir_id(user):

    r = None
    if Crosswalk.objects.filter(user=user).exists():
        c = Crosswalk.objects.get(user=user)
        r = c.fhir_id
    return r
