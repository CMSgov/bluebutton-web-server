from django.contrib import admin

from apps.fhir.server.models import SupportedResourceType


class SupportedResourceTypeAdmin(admin.ModelAdmin):
    
    list_display = ('resource_name', )
    search_fields = ('resource_name', )

admin.site.register(SupportedResourceType, SupportedResourceTypeAdmin)
