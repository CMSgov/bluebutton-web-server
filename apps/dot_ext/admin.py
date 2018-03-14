from django.contrib import admin
from oauth2_provider.models import AccessToken
from oauth2_provider.models import get_application_model


Application = get_application_model()


class MyAccessToken(AccessToken):

    class Meta:
        proxy = True
        app_label = "bluebutton"


class MyApplication(Application):

    class Meta:
        proxy = True
        app_label = "bluebutton"


class MyApplicationAdmin(admin.ModelAdmin):

    list_display = ("name", "user", "authorization_grant_type", "scopes",
                    "skip_authorization", "created", "updated")
    list_filter = ("client_type", "authorization_grant_type",
                   "skip_authorization")
    radio_fields = {
        "client_type": admin.HORIZONTAL,
        "authorization_grant_type": admin.VERTICAL,
    }
    raw_id_fields = ("user", )


admin.site.register(MyApplication, MyApplicationAdmin)


class MyAccessTokenAdmin(admin.ModelAdmin):

    list_display = ('get_user_username', 'get_app_name', 'expires', 'scope')
    search_fields = ('user__username', 'application__name',)
    list_filter = ("user__username", "application__name")

    def get_app_name(self, obj):
        return obj.application.name

    get_app_name.admin_order_field = "name"
    get_app_name.short_description = "Application Name"

    def get_user_username(self, obj):
        return obj.user.username

    get_user_username.admin_order_field = "username"
    get_user_username.short_description = "User Name"


admin.site.register(MyAccessToken, MyAccessTokenAdmin)
