from django.contrib import admin

from .models import ProtectedCapability


class ProtectedCapabilityAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'group')
    search_fields = ('title', 'slug', 'group')

admin.site.register(ProtectedCapability, ProtectedCapabilityAdmin)
