from django.http import JsonResponse
from django.views.decorators.http import require_GET

from oauth2_provider.decorators import protected_resource


@require_GET
@protected_resource()
def openidconnect_userinfo(request):
    """
    Views that returns a json representation of the current user's details.
    """
    user = request.resource_owner
    data = {
        'sub': user.username,
        'name': "%s %s" % (user.first_name, user.last_name),
        'given_name': user.first_name,
        'familty_name': user.last_name,
        'email': user.email,
        'iat': user.date_joined,
    }
    return JsonResponse(data)
