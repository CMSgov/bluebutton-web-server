from oauth2_provider.models import get_application_model
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from apps.messages import APPLICATION_TEMPORARILY_INACTIVE

Application = get_application_model()
User = get_user_model()


def validate_app_and_org(request):

    client_id = None

    if request.GET is not None:
        client_id = request.GET.get('client_id', None)

    if request.POST is not None:
        client_id = request.POST.get('client_id', None)

    app = None
    user = None

    if client_id is not None:
        try:
            app = Application.objects.get(client_id=client_id)
        except Application.DoesNotExist:
            pass

    try:
        user = User.objects.get(pk=app.user_id) if app else None
    except User.DoesNotExist:
        pass

    if app and not app.active:
        raise PermissionDenied(APPLICATION_TEMPORARILY_INACTIVE.format(app.name))

    if user and not user.is_active:
        raise PermissionDenied(APPLICATION_TEMPORARILY_INACTIVE.format(app.name))
