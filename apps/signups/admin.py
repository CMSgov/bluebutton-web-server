from django.contrib import admin
from .models import CertifyingBody

class CertifyingBodyAdmin(admin.ModelAdmin):
    
    list_display =  ('iss', 'title', 'verified')
    search_fields = ('iss', 'title', 'first_name',
                     'last_name', 'organization_name', 'email')
    
admin.site.register(CertifyingBody, CertifyingBodyAdmin)
