from django.contrib import admin

from .models import Endorsement


class EndorsementAdmin(admin.ModelAdmin):
    list_display = ('title', 'iss', 'iat', 'exp', 'signature_verified', 'is_expired')
    search_fields = ('title', 'iss')


admin.site.register(Endorsement, EndorsementAdmin)
