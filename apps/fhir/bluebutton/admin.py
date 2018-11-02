from django.contrib import admin

from apps.fhir.bluebutton.models import Crosswalk


class CrosswalkAdmin(admin.ModelAdmin):
    list_display = ('get_user_username', 'fhir_id', 'get_fhir_source')
    search_fields = ('user__username', 'fhir_id', 'fhir_source__name')
    raw_id_fields = ("user", )

    def get_user_username(self, obj):
        return obj.user.username

    get_user_username.admin_order_field = "username"
    get_user_username.short_description = "User Name"

    def get_fhir_source(self, obj):
        return getattr(obj.fhir_source, 'name', '')

    get_fhir_source.admin_order_field = "name"
    get_fhir_source.short_description = "Name"


admin.site.register(Crosswalk, CrosswalkAdmin)
