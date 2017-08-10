from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ..models import UserProfile
from oauth2_provider.decorators import protected_resource
from collections import OrderedDict

@require_GET
@protected_resource()
def openidconnect_userinfo(request):
    """
    Views that returns a JSON representation of the current user's details.
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
    data['vot'] = up.vot()
    data['ial'] = up.ial
    data['aal'] = up.aal   
    return JsonResponse(data)
