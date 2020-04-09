from apps.fhir.bluebutton.models import Crosswalk
from django.contrib import admin


class CrosswalkAdmin(admin.ModelAdmin):
    list_display = ('get_user_username', 'fhir_id')
    search_fields = ('user__username', '_fhir_id')
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
