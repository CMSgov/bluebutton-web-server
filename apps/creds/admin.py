from django.contrib import admin
from django.contrib.auth.models import User
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
    readonly_fields = ('id', 'get_user', 'get_organization', 'updated_at', 'last_visit', 'visits_count', 'get_creds_req_url',)
    list_display = ("application", "id",
                    "get_user", "get_organization", "get_creds_req_url",
                    "created_at", "updated_at",
                    "last_visit", "visits_count")
    list_filter = ('application__user__username',)

    search_fields = ('application__name', 'application__user__username', '=id')

    raw_id_fields = ("application",)

    def get_user(self, obj):
        usr = None
        app = Application.objects.get(pk=obj.application_id)
        if app:
            usr = User.objects.get(pk=app.user_id)
        return usr

    get_user.admin_order_field = "get_user"
    get_user.short_description = "User of the application"

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

    get_organization.admin_order_field = "get_organization"
    get_organization.short_description = "Organization of the application"

    def get_creds_req_url(self, obj):
        return get_url(obj.id)

    get_creds_req_url.admin_order_field = "get_creds_req_url"
    get_creds_req_url.short_description = "URL for credentials request"
