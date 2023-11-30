from django.contrib import admin

from .models import ProtectedCapability


@admin.register(ProtectedCapability)
class ProtectedCapabilityAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "group")
    search_fields = ("title", "slug", "group")
