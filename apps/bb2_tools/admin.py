from django.conf import settings
from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from oauth2_provider.models import AccessToken, RefreshToken
from oauth2_provider.models import get_application_model

from apps.dot_ext.models import ArchivedToken
from apps.bb2_tools.models import (
    BeneficiaryDashboard,
    MyAccessTokenViewer,
    MyRefreshTokenViewer,
    MyArchivedTokenViewer,
    MyConnectedApplicationViewer,
    AccessTokenStats,
    RefreshTokenStats,
    ArchivedTokenStats,
    DummyAdminObject,
)

BB2_TOOLS_PATH = "/admin/bb2_tools/"
LINK_REF_FMT = "<a  href='{0}{1}?q={2}'>{3}</a>"
TOKEN_VIEWERS = {MyAccessTokenViewer, MyRefreshTokenViewer, MyArchivedTokenViewer}


def get_my_tokens_widget(u):
    widget_html = "<div><ul>"
    for v in TOKEN_VIEWERS:
        widget_html += "<li>"
        widget_html += LINK_REF_FMT.format(BB2_TOOLS_PATH, v.__name__.lower(), u, str(v()._meta.verbose_name_plural))
        widget_html += "</li>"

    widget_html += "</ul></div>"
    return widget_html


class ReadOnlyAdmin(admin.ModelAdmin):
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        return list(self.readonly_fields) + \
            [field.name for field in obj._meta.fields] + \
            [field.name for field in obj._meta.many_to_many]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BeneficiaryDashboard)
class BeneficiaryDashboardAdmin(ReadOnlyAdmin):
    list_display = ('get_user_username', 'get_identities', 'get_access_tokens', 'get_connected_applications', 'date_created')
    search_fields = ('user__username', '_fhir_id', '_user_id_hash', '_user_mbi_hash')
    readonly_fields = ('date_created',)
    raw_id_fields = ("user", )

    def get_queryset(self, request):
        qs = super(BeneficiaryDashboardAdmin, self).get_queryset(request)
        return qs

    def get_user_username(self, obj):
        return obj.user.username

    get_user_username.admin_order_field = "username"
    get_user_username.short_description = "User Name"

    def get_access_tokens(self, obj):
        # use relative URI in ref link to avoid re-login
        return format_html(get_my_tokens_widget(obj.user.username))

    get_access_tokens.admin_order_field = 'MyTokens'
    get_access_tokens.short_description = 'My Tokens'
    get_access_tokens.allow_tags = True

    def get_identities(self, obj):
        return format_html("<div><ul><li>FHIR_ID:{}</li><li>HICN HASH:{}</li><li>MBI HASH:{}</li>".format(
            obj.fhir_id, obj.user_hicn_hash, obj.user_mbi_hash))

    get_identities.admin_order_field = 'MyIdentities'
    get_identities.short_description = 'My Identities'
    get_identities.allow_tags = True

    def get_connected_applications(self, obj):
        inlinehtml = "<div><ul>"
        tokens = MyAccessTokenViewer.objects.filter(
            user=obj.user_id).values("user", "application").annotate(token_count=Count("token"))
        for t in tokens:
            app = get_application_model().objects.get(id=t['application'])
            inlinehtml += "<li>App:{}, Token Count:{}</li>".format(app.name, t['token_count'])

        refreshtokens = MyRefreshTokenViewer.objects.filter(
            user=obj.user_id).values("user", "application").annotate(token_count=Count("token"))
        for t in refreshtokens:
            app = get_application_model().objects.get(id=t['application'])
            inlinehtml += "<li>App:{}, Refresh Token Count:{}</li>".format(app.name, t['token_count'])

        archivedtokens = MyArchivedTokenViewer.objects.filter(
            user=obj.user_id).values("user", "application").annotate(token_count=Count("token"))
        for t in archivedtokens:
            app = get_application_model().objects.get(id=t['application'])
            inlinehtml += "<li>App:{}, Archived Token Count:{}</li>".format(app.name, t['token_count'])

        inlinehtml += "</ul></div>"

        return format_html(inlinehtml)

    get_connected_applications.admin_order_field = 'MyConnectedApps'
    get_connected_applications.short_description = 'My Connected Apps'
    get_connected_applications.allow_tags = True


@admin.register(MyAccessTokenViewer)
class MyAccessTokenViewerAdmin(ReadOnlyAdmin):
    '''
    oauth2_provider_accesstoken:
    id
    token
    expires
    scope
    application_id
    user_id
    created
    updated
    source_refresh_token_id

    '''
    list_display = ('user', 'application', 'expires', 'scope', 'token', 'updated', 'created')
    search_fields = ('user__username', 'application__name', 'token')
    list_filter = ("user", "application")
    raw_id_fields = ("user", 'application')


@admin.register(MyRefreshTokenViewer)
class MyRefreshTokenViewerAdmin(ReadOnlyAdmin):
    '''
    oauth2_provider_refreshtoken:
    id
    token
    access_token_id
    application_id
    user_id
    created
    updated
    revoked
    '''
    list_display = ('user', 'application', 'token', 'access_token_id', 'revoked', 'updated', 'created')
    search_fields = ('user__username', 'application__name', 'token')
    list_filter = ("user", "application")
    raw_id_fields = ("user", 'application')


@admin.register(MyArchivedTokenViewer)
class MyArchivedTokenViewerAdmin(ReadOnlyAdmin):
    '''
    dot_ext_archivedtoken:
    id
    token
    expires
    scope
    created
    updated
    archived_at
    application_id
    user_id
    '''
    list_display = ('user', 'application', 'expires', 'scope', 'token', 'archived_at', 'updated', 'created')
    search_fields = ('user__username', 'application__name', 'token')
    list_filter = ("user", "application")
    raw_id_fields = ("user", 'application')


@admin.register(MyConnectedApplicationViewer)
class MyConnectedApplicationViewerAdmin(ReadOnlyAdmin):
    '''
    oauth2_provider_accesstoken:
    application_id
    user_id
    ...
    dot_ext_archivedtoken:
    application_id
    user_id
    ...
    oauth2_provider_accesstoken:
    application_id
    user_id
    '''
    list_display = ('user', )
    search_fields = ('user__username', 'application__name')
    list_filter = ("user",)
    raw_id_fields = ("user",)

    def get_queryset(self, request):
        qs_tokens = MyAccessTokenViewer.objects.filter(user=request.user)
        qs_refreshtokens = MyRefreshTokenViewer.objects.filter(user=request.user)
        qs_archivedtokens = MyArchivedTokenViewer.objects.filter(user=request.user)
        # return qs.filter(author=request.user)
        return (qs_tokens | qs_refreshtokens | qs_archivedtokens)


@admin.register(DummyAdminObject)
class BlueButtonAPISplunkLauncherAdmin(ReadOnlyAdmin):
    change_list_template = 'admin/bb2_splunk_dashboards_change_list.html'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )
        response.context_data["splunk_dashboards"] = settings.SPLUNK_DASHBOARDS
        return response


@admin.register(AccessTokenStats)
class ConnectedBeneficiaryCountByAppsAdmin(ReadOnlyAdmin):
    change_list_template = 'admin/access_token_counts_by_apps_change_list.html'
    date_hierarchy = 'created'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        # try:
        #     qs = response.context_data['cl'].queryset
        # except (AttributeError, KeyError):
        #     return response

        bene_cnt_by_app = AccessToken.objects.all().values(
            'application__name', 'user__username').annotate(
                tk_cnt=Count('token')).order_by('tk_cnt')

        response.context_data["token_cnts_by_apps"] = bene_cnt_by_app

        return response


@admin.register(RefreshTokenStats)
class RefreshTokenCountByAppsAdmin(ReadOnlyAdmin):
    change_list_template = 'admin/refresh_token_counts_by_apps_change_list.html'
    date_hierarchy = 'created'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        # try:
        #     qs = response.context_data['cl'].queryset
        # except (AttributeError, KeyError):
        #     return response

        refresh_token_cnt_by_app = RefreshToken.objects.all().values(
            'application__name', 'user__username').annotate(
                tk_cnt=Count('token')).order_by('tk_cnt')

        response.context_data["token_cnts_by_apps"] = refresh_token_cnt_by_app

        return response


@admin.register(ArchivedTokenStats)
class ArchivedTokenStatsAdmin(ReadOnlyAdmin):
    change_list_template = 'admin/archived_token_counts_by_apps_change_list.html'
    date_hierarchy = 'created'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        # try:
        #     response.context_data['cl'].queryset
        # except (AttributeError, KeyError):
        #     return response

        archived_token_cnt_by_app = ArchivedToken.objects.all().values(
            'application__name', 'user__username').annotate(
                tk_cnt=Count('token')).order_by('tk_cnt')

        response.context_data["token_cnts_by_apps"] = archived_token_cnt_by_app

        return response
