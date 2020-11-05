from django.conf import settings
from django.contrib import admin
from django.db.models import Count, Min, Max, DateTimeField
from django.db.models.functions import Trunc
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
LINK_REF_FMT = "<a  href='{0}{1}?q={2}&user__id__exact={3}'>{4}</a>"
TOKEN_VIEWERS = {MyAccessTokenViewer, MyRefreshTokenViewer, MyArchivedTokenViewer}


def get_next_in_date_hierarchy(request, date_hierarchy):
    if date_hierarchy + '__day' in request.GET:
        return 'hour'
    if date_hierarchy + '__month' in request.GET:
        return 'day'
    if date_hierarchy + '__year' in request.GET:
        return 'week'
    return 'month'


def get_my_tokens_widget(u, id):
    widget_html = "<div><ul>"
    for v in TOKEN_VIEWERS:
        widget_html += "<li>"
        widget_html += LINK_REF_FMT.format(BB2_TOOLS_PATH, v.__name__.lower(), u, id, str(v()._meta.verbose_name_plural))
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


class TokenCountByAppsAdmin(ReadOnlyAdmin):
    def get_model(self):
        pass

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        clazz_model = self.get_model()
        bene_cnt_by_app = clazz_model.objects.all().values(
            'application__name', 'user__username').annotate(
                tk_cnt=Count('token')).order_by('tk_cnt')

        bene_total = clazz_model.objects.all().aggregate(
            tk_total=Count('token'))

        response.context_data["token_cnts_by_apps"] = bene_cnt_by_app
        response.context_data["bene_total"] = bene_total

        # bene counts over time as bar chart
        period = get_next_in_date_hierarchy(
            request,
            self.date_hierarchy,
        )
        response.context_data['period'] = period
        bene_cnts_over_time = clazz_model.objects.all().annotate(
            period=Trunc(
                'created',
                period,
                output_field=DateTimeField(),
            ),
        ).values('period', 'application__name', 'user__username').annotate(tk_cnt=Count('token')).order_by('period')

        bene_cnts_range = bene_cnts_over_time.aggregate(
            low=Min('tk_cnt'),
            high=Max('tk_cnt'),
        )
        high = bene_cnts_range.get('high', 0)
        low = bene_cnts_range.get('low', 0)
        response.context_data['bene_cnts_over_time'] = [{
            'period': x['period'],
            'tk_cnt': x['tk_cnt'] or 0,
            'pct': (x['tk_cnt'] or 0) / high * 100 if high > low else 0,
        } for x in bene_cnts_over_time]

        return response


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
        return format_html(get_my_tokens_widget(obj.user.username, obj.user.id))

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
    search_fields = ('user__username__exact', 'application__name', 'token')
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
    search_fields = ('user__username__exact', 'application__name', 'token')
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
class ConnectedBeneficiaryCountByAppsAdmin(TokenCountByAppsAdmin):
    change_list_template = 'admin/access_token_counts_by_apps_change_list.html'
    date_hierarchy = 'created'

    def get_model(self):
        return AccessToken

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )
        response.context_data["page_desc"] = {
            "header_app_name": "Application",
            "header_user_name": "User",
            "header_token_count": "Token Count",
            "header_percentage": "Percentage",
        }
        return response


@admin.register(RefreshTokenStats)
class RefreshTokenCountByAppsAdmin(TokenCountByAppsAdmin):
    change_list_template = 'admin/refresh_token_counts_by_apps_change_list.html'
    date_hierarchy = 'created'

    def get_model(self):
        return RefreshToken

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )
        response.context_data["page_desc"] = {
            "header_app_name": "Application",
            "header_user_name": "User",
            "header_token_count": "Token Count",
            "header_percentage": "Percentage",
        }
        return response


@admin.register(ArchivedTokenStats)
class ArchivedTokenStatsAdmin(TokenCountByAppsAdmin):
    change_list_template = 'admin/archived_token_counts_by_apps_change_list.html'
    date_hierarchy = 'created'

    def get_model(self):
        return ArchivedToken

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )
        response.context_data["page_desc"] = {
            "header_app_name": "Application",
            "header_user_name": "User",
            "header_token_count": "Token Count",
            "header_percentage": "Percentage",
        }
        return response
