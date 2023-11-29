from django.contrib import admin
from .models import AnonUserState


@admin.register(AnonUserState)
class AnonUserStateAdmin(admin.ModelAdmin):

    list_display = ("state", "next_uri")
    search_fields = ("state", "next_uri")
