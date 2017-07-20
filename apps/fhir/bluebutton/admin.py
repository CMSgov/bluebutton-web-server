from django.contrib import admin

from apps.fhir.bluebutton.models import (Crosswalk,
                                         # FhirServer,
                                         BlueButtonText)


class CrosswalkAdmin(admin.ModelAdmin):
    list_display = ('user', 'fhir_id', 'fhir_source')
    search_fields = ('user', 'fhir_id', 'fhir_source')


# class FhirServerAdmin(admin.ModelAdmin):
#     list_display = ('name',
#                     'shard_by',
#                     'fhir_url',
#                     'client_auth',
#                     'server_verify')
#     search_fields = ('name', 'fhir_url')


class BlueButtonTextAdmin(admin.ModelAdmin):
    list_display = ('user', 'bb_content')
    search_fields = ('user', )


admin.site.register(Crosswalk, CrosswalkAdmin)
# admin.site.register(FhirServer, FhirServerAdmin)
admin.site.register(BlueButtonText, BlueButtonTextAdmin)
