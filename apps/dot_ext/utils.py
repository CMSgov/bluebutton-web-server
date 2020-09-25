from oauth2_provider.models import get_application_model
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.conf import settings

Application = get_application_model()
User = get_user_model()


def validate_app_is_active(request):

    client_id = None

    if request.GET is not None:
        client_id = request.GET.get('client_id', None)

    if client_id is None and request.POST is not None:
        client_id = request.POST.get('client_id', None)

    app = None

    if client_id is not None:
        try:
            app = Application.objects.get(client_id=client_id)
        except Application.DoesNotExist:
            pass

    if app and not app.active:
        raise PermissionDenied(settings.APPLICATION_TEMPORARILY_INACTIVE.format(app.name))
