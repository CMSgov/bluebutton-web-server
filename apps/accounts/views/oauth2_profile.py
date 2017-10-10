from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ..models import UserProfile
from apps.fhir.bluebutton.models import Crosswalk
from oauth2_provider.decorators import protected_resource
from collections import OrderedDict
from django.contrib.auth.decorators import login_required


@require_GET
@protected_resource()
def openidconnect_userinfo(request):
    """
    OIDC-style userinfo
    """
    user = request.resource_owner
    up = UserProfile.objects.get(user=user)
    data = OrderedDict()
    data['sub'] = user.username
    data['name'] = "%s %s" % (user.first_name, user.last_name)
    data['given_name'] = user.first_name
    data['family_name'] = user.last_name
    data['email'] = user.email
    data['iat'] = user.date_joined
    data['ial'] = up.ial  # experimental
    # data['ial'] = up.ial # experimental
    # data['vot'] = up.vot() # experimental

    # Get the FHIR ID if its there
    fhir_id = get_fhir_id(user)
    if fhir_id:
        data['patient'] = fhir_id

    return JsonResponse(data)


@require_GET
@login_required()
def userinfo_w_login(request):
    """
    OIDC Style userinfo
    """
    user = request.user
    up = UserProfile.objects.get(user=user)
    data = OrderedDict()
    data['sub'] = user.username
    data['name'] = "%s %s" % (user.first_name, user.last_name)
    data['given_name'] = user.first_name
    data['family_name'] = user.last_name
    data['email'] = user.email
    data['iat'] = user.date_joined
    data['iat'] = user.date_joined
    data['ial'] = up.ial     # experimental
    # data['ial'] = up.ial   # experimental
    # data['vot'] = up.vot() # experimental

    # Get the FHIR ID if its there
    fhir_id = get_fhir_id(request.user)
    if fhir_id:
        data['patient'] = fhir_id
    return JsonResponse(data)


def get_fhir_id(user):

    r = None
    if Crosswalk.objects.filter(user=user).exists():
        c = Crosswalk.objects.get(user=user)
        r = c.fhir_id
    return r
