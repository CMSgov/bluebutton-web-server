import json
from django.conf import settings
from django.contrib import admin
from django.db.models import Q, Count, Min, Max, DateTimeField
from django.db.models.functions import Trunc
from django.utils.html import format_html
from oauth2_provider.models import AccessToken, RefreshToken
from oauth2_provider.models import get_application_model

from apps.dot_ext.models import ArchivedToken
from apps.bb2_tools.models import (
    BeneficiaryDashboard,
    ApplicationStats,
    MyAccessTokenViewer,
    MyRefreshTokenViewer,
    MyArchivedTokenViewer,
    AccessTokenStats,
    RefreshTokenStats,
    ArchivedTokenStats,
    DummyAdminObject,
)
from apps.fhir.bluebutton.utils import get_patient_by_id

BB2_TOOLS_PATH = "/admin/bb2_tools/"
LINK_REF_FMT = "<a  href='{0}{1}?q={2}&user__id__exact={3}'>{4}</a>"
TOKEN_VIEWERS = {MyAccessTokenViewer, MyRefreshTokenViewer, MyArchivedTokenViewer}


def gen_ctx_grp_by_date_fld(request, uniq_fld_name, date_fld_name, clazz_model, date_hierarchy):
    period = get_next_in_date_hierarchy(
        request,
        date_hierarchy,
    )
    aggregate_by_period_ctx = {}
    aggregate_by_period_ctx['period'] = period

    total_by_date = clazz_model.objects.all().annotate(
        period=Trunc(
            date_fld_name,
            period,
            output_field=DateTimeField(),
        ),
    ).values('period').annotate(sub_total=Count(uniq_fld_name)).order_by('period')

    sub_totals_range = total_by_date.aggregate(
        low=Min('sub_total'),
        high=Max('sub_total'),
    )

    high = sub_totals_range.get('high', 0)
    low = sub_totals_range.get('low', 0)
    chart_list = []
    for e in total_by_date:
        chart_list.append(
            {'period': e['period'],
             'sub_total': e['sub_total'] or 0,
             'pct': (e['sub_total'] or 0) / high * 100 if high > low else 0, })
    return chart_list


def gen_ctx_grp_by_flds(clazz_model, grp_flds, uniq_fld, marked_fld_name, marked_fld_val):
    row_cnts_grp_by = clazz_model.objects.all().values(
        *grp_flds).annotate(
            row_cnt=Count(uniq_fld)).order_by('row_cnt')

    row_cnts_range = row_cnts_grp_by.aggregate(
        low=Min('row_cnt'),
        high=Max('row_cnt'),
    )

    high = row_cnts_range.get('high', 0)
    low = row_cnts_range.get('low', 0)
    chart_data_list = []
    for x in row_cnts_grp_by:
        item = {
            'row_cnt': x['row_cnt'] or 0,
            'pct': (x['row_cnt'] or 0) / high * 100 if high > low else 0,
        }
        if x[marked_fld_name] == marked_fld_val:
            item['marked'] = True
        grp_by_item = {}
        for y in grp_flds:
            grp_by_item[y] = x[y]
        item.update(grp_by_item)
        chart_data_list.append(item)
    return chart_data_list


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

        # common aggregations for access token, refresh token, archived token
        token_cnts_by_app = clazz_model.objects.all().values(
            'application__name').annotate(
                tk_cnt=Count('token')).order_by('application__name')

        token_total = clazz_model.objects.all().count()

        response.context_data["token_total"] = token_total

        token_cnts_range = token_cnts_by_app.aggregate(
            low=Min('tk_cnt'),
            high=Max('tk_cnt'),
        )

        high = token_cnts_range.get('high', 0)
        low = token_cnts_range.get('low', 0)

        token_no_demo_dict = {}
        token_no_demo_total = 0
        chart_list = []
        table_list = []
        if clazz_model == AccessToken or clazz_model == ArchivedToken:
            # aggregations for access token and archived token only - without demographic scopes
            token_no_demo_cnts_by_app = clazz_model.objects.filter(
                ~Q(scope__icontains="patient/Patient.read")).values(
                'application__name').annotate(
                    tk_cnt=Count('token')).order_by('application__name')
            token_no_demo_total = clazz_model.objects.filter(
                ~Q(scope__icontains="patient/Patient.read")).count()
            response.context_data['token_no_demo_total'] = token_no_demo_total
            for t in token_no_demo_cnts_by_app:
                token_no_demo_dict[t['application__name']] = t['tk_cnt']
            response.context_data['has_demo_scope_cnts'] = True
            for x in token_cnts_by_app:
                no_demo_cnt = token_no_demo_dict.get(x['application__name'])
                demo_cnt = x['tk_cnt'] - (0 if no_demo_cnt is None else no_demo_cnt)
                table_list.append({'application__name': x['application__name'],
                                   'tk_cnt': x['tk_cnt'] or 0,
                                   'no_demo_tk_cnt': no_demo_cnt or 0, })
                chart_list.append({'application__name': x['application__name'],
                                   'tk_cnt': x['tk_cnt'] or 0,
                                   'no_demo_tk_cnt': no_demo_cnt or 0,
                                   'no_demo_pct': (no_demo_cnt or 0) / high * 100 if high > low else 0,
                                   'pct': (demo_cnt or 0) / high * 100 if high > low else 0, })
        else:
            response.context_data['has_demo_scope_cnts'] = False
            for x in token_cnts_by_app:
                table_list.append({'application__name': x['application__name'],
                                   'tk_cnt': x['tk_cnt'] or 0, })
                chart_list.append({'application__name': x['application__name'],
                                   'tk_cnt': x['tk_cnt'] or 0,
                                   'pct': (x['tk_cnt'] or 0) / high * 100 if high > low else 0, })

        response.context_data["token_cnts_by_apps"] = table_list
        response.context_data['token_cnts_by_app_chart'] = chart_list

        return response


@admin.register(BeneficiaryDashboard)
class BeneficiaryDashboardAdmin(ReadOnlyAdmin):
    change_form_template = 'admin/bb2_bene_dashboard_change_form.html'
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

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        crosswalk = BeneficiaryDashboard.objects.get(pk=int(object_id))

        json_resp = None

        try:
            json_resp = get_patient_by_id(crosswalk.fhir_id, request)
        except Exception as e:
            json_resp = {"backend_error": str(e)}

        extra_context['warning_label'] = {
            "pii_warning_text": ("This page might contain sensitive"
                                 " identity information when deployed in production, "
                                 "and is only for personnel with access permission.")}
        extra_context['info_from_bfd'] = json.dumps(json_resp, sort_keys=True, indent=4)
        return super(BeneficiaryDashboardAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context,
        )


@admin.register(MyAccessTokenViewer)
class MyAccessTokenViewerAdmin(ReadOnlyAdmin):
    list_display = ('user', 'application', 'expires', 'scope', 'token', 'updated', 'created')
    search_fields = ('user__username__exact', 'application__name', 'token')
    raw_id_fields = ("user", 'application')


@admin.register(MyRefreshTokenViewer)
class MyRefreshTokenViewerAdmin(ReadOnlyAdmin):
    list_display = ('user', 'application', 'token', 'access_token_id', 'revoked', 'updated', 'created')
    search_fields = ('user__username__exact', 'application__name', 'token')
    raw_id_fields = ("user", 'application')


@admin.register(MyArchivedTokenViewer)
class MyArchivedTokenViewerAdmin(ReadOnlyAdmin):
    list_display = ('user', 'application', 'expires', 'scope', 'token', 'archived_at', 'updated', 'created')
    search_fields = ('user__username', 'application__name', 'token')
    raw_id_fields = ("user", 'application')


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


@admin.register(ApplicationStats)
class ApplicationStatsAdmin(ReadOnlyAdmin):
    change_list_template = 'admin/apps_stats_change_list.html'
    list_display = ("name", "user", "authorization_grant_type", "client_id",
                    "require_demographic_scopes", "scopes",
                    "created", "updated", "skip_authorization")
    radio_fields = {
        "client_type": admin.HORIZONTAL,
        "authorization_grant_type": admin.VERTICAL,
    }

    date_hierarchy = 'created'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        clazz_model = ApplicationStats
        total = clazz_model.objects.all().count()
        panels = []

        # apps counts over signed up time as bar chart
        app_grp_by_created_date_ctx = gen_ctx_grp_by_date_fld(request,
                                                              'name',
                                                              'created',
                                                              clazz_model,
                                                              self.date_hierarchy)
        top_panel = {
            'type': 'bar-chart',
            'title': 'Apps Count by Signup Date: Bar Chart',
            'body': app_grp_by_created_date_ctx,
        }

        # bar chart top: apps count by sign up date
        # bar chart 2nd row left: apps count group be active field
        # bar chart 2nd row center: apps opt in demo info vs apps opt out of demo info
        # bar chart 2nd row right: apps counts group be grant_type + client_type
        # table view bottom: apps count by sign up date
        panels.append(top_panel)
        center_panel = []
        center_panel.append({'body': gen_ctx_grp_by_flds(
            clazz_model,
            ['active'],
            'name', 'active', False),
            'tooltip_txt': ['active is False', 'active is True'],
            'title': 'Apps Count by Active Flag',
            'tooltip_label': 'App group by "active"'})

        center_panel.append({'body': gen_ctx_grp_by_flds(
            clazz_model,
            ['require_demographic_scopes'],
            'name', 'require_demographic_scopes', False),
            'tooltip_txt': ['require_demographic_scopes is False', 'require_demographic_scopes is True'],
            'title': 'Apps Count by Demographic Choice',
            'tooltip_label': 'App group by "require_demographic_scopes"'})

        center_panel.append({'body': gen_ctx_grp_by_flds(
            clazz_model,
            ['client_type', 'authorization_grant_type'],
            'name', 'client_type', 'public'),
            'tooltip_txt': ['client_type is public', 'client type is not public'],
            'title': 'Apps Count by Client & Grant Type',
            'tooltip_label': 'App group by client type, grant type'})

        panels.append({'type': 'horiz-charts', 'data': center_panel})

        bottom_panel = {
            'type': 'table-view',
            'title': 'Apps Count by Signup Date: Tabular View',
            'header': ['Period', 'Apps Count', 'Percentage'],
            'body': app_grp_by_created_date_ctx,
            'total': total,
            'footer': ['Total', total, '100%'],
        }

        panels.append(bottom_panel)
        response.context_data['panels'] = panels

        return response


@admin.register(AccessTokenStats)
class ConnectedBeneficiaryCountByAppsAdmin(TokenCountByAppsAdmin):
    change_list_template = 'admin/token_counts_by_apps_change_list.html'
    # date_hierarchy = 'created'

    def get_model(self):
        return AccessToken

    def changelist_view(self, request, extra_context=None):

        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        response.context_data["page_desc"] = {
            "header_app_name": "Application",
            "header_token_count": "Token Count",
            "header_percentage": "%",
            "header_no_demo_token_count": "Token Count (No Demo Scopes)",
            "header_no_demo_percentage": "%(No Demo Scopes)",
            "bar_chart_title": "Access Token Count by Apps: Bar Chart",
            "bar_chart_no_demo_title": "Access Token Count (No Demo Scope) by Apps: Bar Chart",
            "table_view_title": "Access Token Count by Apps: Tabular View",
        }
        return response


@admin.register(RefreshTokenStats)
class RefreshTokenCountByAppsAdmin(TokenCountByAppsAdmin):
    change_list_template = 'admin/token_counts_by_apps_change_list.html'
    # date_hierarchy = 'created'

    def get_model(self):
        return RefreshToken

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )
        response.context_data["page_desc"] = {
            "header_app_name": "Application",
            "header_token_count": "Token Count",
            "header_percentage": "%",
            "bar_chart_title": "Refresh Token Count by Apps: Bar Chart",
            "table_view_title": "Refresh Token Count by Apps: Tabular View",
        }
        return response


@admin.register(ArchivedTokenStats)
class ArchivedTokenStatsAdmin(TokenCountByAppsAdmin):
    change_list_template = 'admin/token_counts_by_apps_change_list.html'
    # date_hierarchy = 'created'

    def get_model(self):
        return ArchivedToken

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )
        response.context_data["page_desc"] = {
            "header_app_name": "Application",
            "header_token_count": "Token Count",
            "header_percentage": "%",
            "header_no_demo_token_count": "Token Count (No Demo Scopes)",
            "header_no_demo_percentage": "%(No Demo Scopes)",
            "bar_chart_title": "Archived Token Count by Apps: Bar Chart",
            "table_view_title": "Archived Token Count by Apps: Tabular View",
        }
        return response
