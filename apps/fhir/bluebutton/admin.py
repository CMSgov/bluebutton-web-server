from apps.fhir.bluebutton.models import ArchivedCrosswalk, Crosswalk
from django.contrib import admin


@admin.register(Crosswalk)
class CrosswalkAdmin(admin.ModelAdmin):
    list_display = ("get_user_username", "fhir_id")
    search_fields = ("user__username", "_fhir_id")
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
        "_fhir_id",
        "user_id_type",
        "_user_id_hash",
        "_user_mbi_hash",
        "_user_mbi",
    )
    search_fields = ("_fhir_id", "username", "_user_id_hash", "_user_mbi_hash", "_user_mbi")
