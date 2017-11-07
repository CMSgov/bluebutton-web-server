from django.contrib import admin
from .models import Consent


class ConsentAdmin(admin.ModelAdmin):

    list_display = ('myuser', 'application', 'created', 'modified')
    search_fields = ('user', 'application', )
    raw_id_fields = ("user", "application")

    # def app_name(self, instance):
    #     return instance.application.name
    #
    # def user_name(self, instance):
    #     name = '%s %s (%s)' % (instance.user.first_name,
    #                            instance.user.last_name,
    #                            instance.user.username)
    #     return name


admin.site.register(Consent, ConsentAdmin)
