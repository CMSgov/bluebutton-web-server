from django.contrib import admin
from .models import DataAccessGrant


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
        "application",
        "beneficiary",
    )


admin.site.register(DataAccessGrant, DataAccessGrantAdmin)
