from django.contrib import admin

from apps.fhir.bluebutton.models import (Crosswalk)


class CrosswalkAdmin(admin.ModelAdmin):
    list_display = ('user', 'fhir_id', 'fhir_source')
    search_fields = ('user', 'fhir_id', 'fhir_source')


admin.site.register(Crosswalk, CrosswalkAdmin)
