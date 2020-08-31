from oauth2_provider.models import get_application_model
from django.contrib.auth import get_user_model

Application = get_application_model()
User = get_user_model()


def get_app_and_org(request):
    client_id = request.GET.get('client_id', None)
    app = None
    user = None

    if client_id is not None:
        apps = Application.objects.filter(client_id=client_id)
        if apps:
            app = apps.first()
            user = User.objects.get(pk=app.user_id)

    return app, user
