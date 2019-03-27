from waffle.admin import FlagAdmin
from apps.core.models import Flag
from django.contrib import admin

admin.site.register(Flag, FlagAdmin)
