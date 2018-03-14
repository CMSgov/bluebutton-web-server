from django.contrib import admin
from oauth2_provider.models import AccessToken
from oauth2_provider.models import get_application_model

Application = get_application_model()


class MyAccessToken(AccessToken):

    class Meta:
        proxy = True


class MyApplication(Application):

    class Meta:
        proxy = True


class MyApplicationAdmin(admin.ModelAdmin):

    list_display = ("user", "authorization_grant_type", "scopes",
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

    list_display = ('user', 'application', 'expires', 'scope')
    search_fields = ('user__username', 'application__name',)
    list_filter = ("user__username", "application__name")
    raw_id_fields = ("user", 'application')


admin.site.register(MyAccessToken, MyAccessTokenAdmin)
