from django.contrib import admin
from .models import ArchivedDataAccessGrant, DataAccessGrant


class DataAccessGrantAdmin(admin.ModelAdmin):
    list_display = (
        "application",
        "beneficiary",
        "expiration_date",
        "created_at",
    )

    list_filter = (
        "created_at",
        "expiration_date",
    )

    search_fields = (
        "application__name",
        "beneficiary__username",
    )


class ArchivedDataAccessGrantAdmin(admin.ModelAdmin):
    list_display = (
        "application",
        "beneficiary",
        "expiration_date",
        "created_at",
    )

    list_filter = (
        "created_at",
        "expiration_date",
    )

    search_fields = (
        "application__name",
        "beneficiary__username",
    )


admin.site.register(DataAccessGrant, DataAccessGrantAdmin)
admin.site.register(ArchivedDataAccessGrant, ArchivedDataAccessGrantAdmin)
