from django.contrib import admin
from oauth2_provider.models import AccessToken, get_application_model

from apps.dot_ext.csv import ExportCsvMixin
from apps.dot_ext.forms import CreateApplicationForm, EditApplicationForm
from apps.dot_ext.models import ApplicationLabel, AuthFlowUuid, InternalApplicationLabelsProxy

Application = get_application_model()


class MyAccessToken(AccessToken):
    class Meta:
        proxy = True
        app_label = 'bluebutton'


class MyApplication(Application):
    class Meta:
        proxy = True
        app_label = 'bluebutton'


class MyAuthFlowUuid(AuthFlowUuid):
    class Meta:
        proxy = True
        app_label = 'bluebutton'


class CreateNewApplication(Application):
    class Meta:
        proxy = True
        app_label = 'bluebutton'


@admin.register(MyApplication)
class MyApplicationAdmin(admin.ModelAdmin, ExportCsvMixin):
    def get_form(self, request, obj=None, **kwargs):
        """
        Override the get_form method to use different forms for creating and updating applications.
        """
        if obj is None:
            kwargs['form'] = CreateApplicationForm
        else:
            kwargs['form'] = EditApplicationForm

        return super().get_form(request, obj, **kwargs)

    def get_list_display(self, request):
        return (
            'name',
            'get_data_access_type',
            'user',
            'client_id',
            'require_demographic_scopes',
            'scopes',
            'created',
            'updated',
            'active',
            'skip_authorization',
            'get_internal_application_labels',
            'allowed_auth_type',
            'jwks_uri',
            'part_d_eob_only',
        )

    list_filter = (
        'data_access_type',
        'require_demographic_scopes',
        'active',
        'skip_authorization',
        'internal_application_labels',
    )

    radio_fields = {
        'client_type': admin.HORIZONTAL,
        'authorization_grant_type': admin.VERTICAL,
    }

    def get_search_fields(self, request):
        return (
            'name',
            'data_access_type',
            'user__username',
            'internal_application_labels__label',
            '=client_id',
            '=require_demographic_scopes',
            '=authorization_grant_type',
        )

    def get_export_fields(self, request):
        return (
            'id',
            'user',
            'name',
            'created',
            'website_uri',
            'redirect_uris',
            'logo_uri',
            'tos_uri',
            'policy_uri',
            'contacts',
            'support_email',
            'support_phone_number',
            'description',
            'active',
            'first_active',
            'last_active',
            'require_demographic_scopes',
            'data_access_type',
            'internal_application_labels',
            'allowed_auth_type',
            'jwks_uri',
            'part_d_eob_only',
        )

    raw_id_fields = ('user',)

    actions = ['export_as_csv']

    @admin.display(description='Data Access Type')
    def get_data_access_type(self, obj):
        return obj.data_access_type

    @admin.display(description='Internal Application Labels')
    def get_internal_application_labels(self, obj):
        return obj.get_internal_application_labels()


@admin.register(CreateNewApplication)
class CreateNewApplicationAdmin(admin.ModelAdmin):
    form = CreateApplicationForm
    list_display = (
        'name',
        'user',
        'client_id',
        'created',
        'updated',
        'active',
        'skip_authorization',
        'get_internal_application_labels',
        'allowed_auth_type',
        'jwks_uri',
        'part_d_eob_only',
    )
    list_filter = (
        'client_type',
        'active',
        'skip_authorization',
    )

    search_fields = (
        'name',
        'user__username',
        '=client_id',
        'internal_application_labels__label',
    )

    raw_id_fields = ('user',)

    @admin.display(description='Internal Application Labels')
    def get_internal_application_labels(self, obj):
        return obj.get_internal_application_labels()


@admin.register(MyAccessToken)
class MyAccessTokenAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'application',
        'expires',
        'scope',
        'token',
        'get_source_refresh_token',
    )
    search_fields = (
        'user__username',
        'application__name',
        'token',
        'source_refresh_token__token',
    )
    raw_id_fields = ('user', 'application', 'source_refresh_token')

    @admin.display(
        description='Source Refresh Token',
        ordering='token',
    )
    def get_source_refresh_token(self, obj):
        return obj.source_refresh_token.token if obj.source_refresh_token else None


@admin.register(MyAuthFlowUuid)
class MyAuthFlowUuidAdmin(admin.ModelAdmin):
    list_display = (
        'created',
        'auth_uuid',
        'state',
        'code',
        'client_id',
        'auth_pkce_method',
        'auth_crosswalk_action',
        'auth_share_demographic_scopes',
        'auth_share_samhsa_data',
    )
    search_fields = ('auth_uuid', 'state', 'code')


@admin.register(ApplicationLabel)
class ApplicationLabelAdmin(admin.ModelAdmin):
    model = ApplicationLabel
    filter_horizontal = ('applications',)
    list_display = ('name', 'slug', 'short_description')
    list_filter = ('name', 'slug')


@admin.register(InternalApplicationLabelsProxy)
class InternalApplicationLabelAdmin(admin.ModelAdmin):
    list_display = ('label', 'slug', 'description')
