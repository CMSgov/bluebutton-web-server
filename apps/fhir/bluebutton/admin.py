from apps.fhir.bluebutton.models import ArchivedCrosswalk, Crosswalk
from django.contrib import admin


@admin.register(Crosswalk)
class CrosswalkAdmin(admin.ModelAdmin):
    list_display = ("get_user_username", "fhir_id_v2", "fhir_id_v3")
    search_fields = ("user__username", "fhir_id_v2", "fhir_id_v3")
    raw_id_fields = ("user",)

    @admin.display(
        description="User Name",
        ordering="username",
    )
    def get_user_username(self, obj):
        return obj.user.username


@admin.register(ArchivedCrosswalk)
class ArchivedCrosswalkAdmin(admin.ModelAdmin):
    list_display = (
        "archived_at",
        "username",
        "fhir_id_v2",
        "fhir_id_v3",
        "user_id_type",
        "_user_id_hash",
        "_user_mbi_hash",
    )
    search_fields = ("fhir_id_v2", "fhir_id_v3", "username", "_user_id_hash", "_user_mbi_hash")
