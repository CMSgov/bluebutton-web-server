from django.contrib import admin

from apps.fhir.bluebutton.models import (ResourceTypeControl,
                                         Crosswalk,
                                         FhirServer)


class CrosswalkAdmin(admin.ModelAdmin):
    list_display = ('user', 'fhir_id', 'fhir_source')
    search_fields = ('user', 'fhir_id', 'fhir_source')


class FhirServerAdmin(admin.ModelAdmin):
    list_display = ('name', 'shard_by', 'fhir_url')
    search_fields = ('name', 'fhir_url')


class ResourceTypeControlAdmin(admin.ModelAdmin):
    list_display = ('resource_name',)
    search_fields = ('resource_name', 'search_block', 'search_add')


admin.site.register(Crosswalk, CrosswalkAdmin)
admin.site.register(FhirServer, FhirServerAdmin)
admin.site.register(ResourceTypeControl, ResourceTypeControlAdmin)
