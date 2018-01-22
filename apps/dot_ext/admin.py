from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered, NotRegistered
from oauth2_provider.models import get_application_model

Application = get_application_model()

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "client_type", "authorization_grant_type", "created", "updated")
    list_filter = ("client_type", "authorization_grant_type", "skip_authorization")
    radio_fields = {
        "client_type": admin.HORIZONTAL,
        "authorization_grant_type": admin.VERTICAL,
    }
    raw_id_fields = ("user", )


admin.site.register(Application, ApplicationAdmin)

