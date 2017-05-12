from django.contrib import admin

from apps.fhir.server.models import (SupportedResourceType,
                                     ResourceRouter)


class SupportedResourceTypeAdmin(admin.ModelAdmin):
    list_display = ('resource_name', 'resourceType')
    search_fields = ('resource_name', 'resourceType')


class ResourceRouterAdmin(admin.ModelAdmin):
    list_display = ('name',
                    'fhir_url',
                    'shard_by',
                    'get_resources',
                    'open_r_count',
                    'protected_r_count',
                    'client_auth',
                    'server_verify')  # 'fhir_path')
    search_fields = ('name', 'fhir_url')

    def protected_r_count(self, obj):
        return "%s" % obj.get_protected_resource_count()

    protected_r_count.short_description = "Protected"

    def open_r_count(self, obj):
        return "%s" % obj.get_open_resource_count()

    open_r_count.short_description = 'Open'


admin.site.register(SupportedResourceType, SupportedResourceTypeAdmin)
admin.site.register(ResourceRouter, ResourceRouterAdmin)
