from django.contrib import admin

from apps.fhir.server.models import SupportedResourceType, ResourceTypeControl


class SupportedResourceTypeAdmin(admin.ModelAdmin):
    
    list_display =  ('resource_name', )
    search_fields = ('resource_name', )
    

class ResourceTypeControlAdmin(admin.ModelAdmin):

    list_display = ('resource_name',)
    search_fields = ('resource_name', 'search_block', 'search_add')


admin.site.register(SupportedResourceType, SupportedResourceTypeAdmin)
admin.site.register(ResourceTypeControl, ResourceTypeControlAdmin)

