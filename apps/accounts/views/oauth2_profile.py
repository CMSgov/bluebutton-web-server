from django.http import JsonResponse
from django.views.decorators.http import require_GET

from oauth2_provider.decorators import protected_resource


@require_GET
@protected_resource()
def user_self(request):
    """
    Views that returns a json representation of the current user's details.
    """
    user = request.resource_owner
    data = {
        'id': user.pk,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'created': user.date_joined,
    }
    return JsonResponse(data)
