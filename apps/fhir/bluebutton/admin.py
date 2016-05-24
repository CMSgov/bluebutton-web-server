from django.contrib import admin

# Register your models here.

from apps.fhir.bluebutton.models import ResourceTypeControl

class ResourceTypeControlAdmin(admin.ModelAdmin):

    list_display = ('resource_name',)
    search_fields = ('resource_name', 'search_block', 'search_add')


admin.site.register(ResourceTypeControl, ResourceTypeControlAdmin)

