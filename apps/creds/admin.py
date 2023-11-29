from django.contrib import admin
from django.contrib.auth.models import User
from oauth2_provider.generators import generate_client_secret
from oauth2_provider.models import get_application_model

from apps.accounts.models import UserProfile

from .models import CredentialingReqest
from .utils import get_url

Application = get_application_model()


class MyCredentialingRequest(CredentialingReqest):
    class Meta:
        proxy = True
        app_label = "bluebutton"


@admin.register(MyCredentialingRequest)
class MyCredentialingRequestAdmin(admin.ModelAdmin):
    readonly_fields = (
        "id",
        "get_user",
        "get_organization",
        "updated_at",
        "last_visit",
        "visits_count",
        "get_creds_req_url",
    )
    list_display = (
        "application",
        "id",
        "get_user",
        "get_organization",
        "get_creds_req_url",
        "created_at",
        "updated_at",
        "last_visit",
        "visits_count",
    )

    list_filter = ("application__name",)

    search_fields = ("application__name", "=id")

    raw_id_fields = ("application",)

    @admin.display(
        description="User of the application",
        ordering="get_user",
    )
    def get_user(self, obj):
        usr = None
        app = Application.objects.get(pk=obj.application_id)
        if app:
            usr = User.objects.get(pk=app.user_id)
        return usr

    @admin.display(
        description="Organization of the application",
        ordering="get_organization",
    )
    def get_organization(self, obj):
        organization = None
        usr = None
        app = Application.objects.get(pk=obj.application_id)
        if app:
            usr = User.objects.get(pk=app.user_id)
        if usr:
            usrprofile = UserProfile.objects.get(user=usr)
            if usrprofile:
                organization = usrprofile.organization_name
        return organization

    @admin.display(
        description="URL for credentials request",
        ordering="get_creds_req_url",
    )
    def get_creds_req_url(self, obj):
        return get_url(obj.id)

    def save_model(self, request, obj, form, change):
        app = Application.objects.get(id=obj.application.id)
        app.client_secret = generate_client_secret()
        app.save()
        super().save_model(request, obj, form, change)
