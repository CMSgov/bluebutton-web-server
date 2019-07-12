from apps.fhir.bluebutton.models import Crosswalk, check_crosswalks, update_crosswalks
from django.contrib import admin
from waffle import switch_is_active


def update(modeladmin, request, queryset):
    '''  NOTE: This function only used for the one-time
         migration for DPR switch-over
    '''
    update_crosswalks()


update.short_description = "Update Crosswalks to negative ID values for DPR switch-over. NOTE: SPECIAL CASE USE!"


class CrosswalkAdmin(admin.ModelAdmin):
    list_display = ('get_user_username', 'fhir_id', 'get_fhir_source')
    search_fields = ('user__username', 'fhir_id', 'fhir_source__name')
    raw_id_fields = ("user", )

    def get_user_username(self, obj):
        return obj.user.username

    get_user_username.admin_order_field = "username"
    get_user_username.short_description = "User Name"

    def get_fhir_source(self, obj):
        return getattr(obj.fhir_source, 'name', '')

    get_fhir_source.admin_order_field = "name"
    get_fhir_source.short_description = "Name"

    def get_actions(self, request):
        actions = super().get_actions(request)
        # Does the waffle feature switch exist to allow this?
        if switch_is_active('admin_crosswalk_dpr_sync'):
            '''  NOTE: This action only used for the one-time
                 migration for DPR switch-over
            '''
            current_state = check_crosswalks()
            current_state_text = ": {} negative (synth) patient IDs, {} Positive (real) patient IDs".format(
                current_state["synthetic"],
                current_state["real"])

            actions[update.__name__] = (update,
                                        update.__name__,
                                        update.short_description + current_state_text)

        return actions


admin.site.register(Crosswalk, CrosswalkAdmin)
