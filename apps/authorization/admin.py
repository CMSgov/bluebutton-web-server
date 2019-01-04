from django.contrib import admin
from .models import (
    DataAccessGrant,
    update_grants,
    check_grants,
)


def sync(modeladmin, request, queryset):
    update_grants()


sync.short_description = "Sync Data Access Grants to existing Tokens"


class DataAccessGrantAdmin(admin.ModelAdmin):

    def get_actions(self, request):
        actions = super().get_actions(request)
        current_state = check_grants()
        current_state_text = ": {} unique AccessTokens, {} Data Access Grants".format(
            current_state["unique_tokens"],
            current_state["grants"])

        actions[sync.__name__] = (sync,
                                  sync.__name__,
                                  sync.short_description + current_state_text)
        return actions


admin.site.register(DataAccessGrant, DataAccessGrantAdmin)
