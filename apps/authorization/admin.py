from django.contrib import admin
from .models import DataAccessGrant

class DataAccessGrantAdmin(admin.ModelAdmin):
    pass

admin.site.register(DataAccessGrant, DataAccessGrantAdmin)
