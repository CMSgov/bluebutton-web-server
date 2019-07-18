from apps.fhir.bluebutton.models import Crosswalk, check_crosswalks, convert_crosswalks_to_synthetic
from django.contrib import admin
from waffle import switch_is_active


def convert(modeladmin, request, queryset):
    '''  NOTE: This function only used for the one-time
         migration for DPR switch-over
    '''
    # Note: Hash for allowed FHIR server passed in below:
    convert_crosswalks_to_synthetic("e40546d58a288cc6b973a62a8d1e5f1103f468f435011e28f5dc7b626de8e69e")


convert.short_description = "Convert Crosswalks to negative ID values for DPR switch-over. NOTE: SPECIAL CASE USE!"


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

            actions[convert.__name__] = (convert,
                                         convert.__name__,
                                         convert.short_description + current_state_text)

        return actions


admin.site.register(Crosswalk, CrosswalkAdmin)
