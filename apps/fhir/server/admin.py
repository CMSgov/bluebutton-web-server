from django.contrib import admin

from apps.fhir.server.models import (SupportedResourceType,
                                     ResourceRouter)


class SupportedResourceTypeAdmin(admin.ModelAdmin):
    list_display = ('resource_name',)
    search_fields = ('resource_name',)


class ResourceRouterAdmin(admin.ModelAdmin):
    list_display = ('supported_resource', 'fhir_path')
    search_fields = ('supported_resource', )


admin.site.register(SupportedResourceType, SupportedResourceTypeAdmin)
admin.site.register(ResourceRouter, ResourceRouterAdmin)
