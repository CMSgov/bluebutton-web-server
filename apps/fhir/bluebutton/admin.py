from apps.fhir.bluebutton.models import ArchivedCrosswalk, Crosswalk
from django.contrib import admin


class CrosswalkAdmin(admin.ModelAdmin):
    list_display = ('get_user_username', 'fhir_id')
    search_fields = ('user__username', '_fhir_id')
    raw_id_fields = ("user", )

    def get_user_username(self, obj):
        return obj.user.username

    get_user_username.admin_order_field = "username"
    get_user_username.short_description = "User Name"


admin.site.register(Crosswalk, CrosswalkAdmin)


class ArchivedCrosswalkAdmin(admin.ModelAdmin):
    list_display = ('archived_at', 'get_crosswalk_id', '_fhir_id', 'user_id_type', '_user_id_hash', '_user_mbi_hash')
    search_fields = ('get_crosswalk_id', '_fhir_id', '_user_id_hash', '_user_mbi_hash')
    raw_id_fields = ("crosswalk", )

    def get_crosswalk_id(self, obj):
        return obj.crosswalk.id


admin.site.register(ArchivedCrosswalk, ArchivedCrosswalkAdmin)
