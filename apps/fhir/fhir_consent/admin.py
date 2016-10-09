from django.contrib import admin

from .models import fhir_Consent


class fhir_ConsentAdmin(admin.ModelAdmin):

    list_display = ('id', 'key', 'user_name', 'app_name', 'created', 'revoked')
    search_fields = ('key', 'id', )

    def app_name(self, instance):
        return instance.application.name

    def user_name(self, instance):
        name = '%s %s (%s)' % (instance.user.first_name,
                               instance.user.last_name,
                               instance.user.username)
        return name

admin.site.register(fhir_Consent, fhir_ConsentAdmin)
