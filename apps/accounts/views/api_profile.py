from django.views.decorators.http import require_GET
from oauth2_provider.decorators import protected_resource
from django.http import JsonResponse

# TODO is this used?
@require_GET
@protected_resource()
def my_profile(request):
    """
    View that returns a JSON representation of the current user's details.
    This is typically called right after the initial authorization.
    """
    user = request.resource_owner
    data = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'created': user.date_joined,
    }
    return JsonResponse(data)
