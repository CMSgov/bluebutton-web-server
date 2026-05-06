from django.contrib import admin
from waffle.admin import FlagAdmin

from apps.core.models import Flag

admin.site.register(Flag, FlagAdmin)
