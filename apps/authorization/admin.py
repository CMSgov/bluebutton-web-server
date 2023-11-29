from django.contrib import admin
from .models import ArchivedDataAccessGrant, DataAccessGrant


@admin.register(DataAccessGrant)
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


@admin.register(ArchivedDataAccessGrant)
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
