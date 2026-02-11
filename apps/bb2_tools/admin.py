import json
from django.conf import settings
from django.contrib import admin
from django.db.models import Q, Count, Min, Max, DateTimeField
from django.db.models.functions import Trunc
from django.utils.html import format_html
from oauth2_provider.models import AccessToken, RefreshToken
from oauth2_provider.models import get_application_model

from apps.accounts.models import UserProfile
from apps.dot_ext.models import ArchivedToken
from apps.bb2_tools.constants import BB2_TOOLS_PATH, LINK_REF_FMT, TOKEN_VIEWERS
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
    UserStats,
)
from apps.fhir.bluebutton.utils import get_v2_patient_by_id


def extract_date_range(response):
    """
    helper to extract date range from cl (changelist) date_hirarchy filter
    expect date_hirarchy.field >= startdate AND date_hirarchy.field < enddate
    or none (date hirarchy filter not clicked)
    """
    startdate = None
    lower_bound_op = None
    enddate = None
    upper_bound_op = None

    qs = None

    try:
        qs = response.context_data["cl"].queryset
    except (AttributeError, KeyError):
        # proceed without info in response
        pass

    q = qs.query
    if hasattr(q, "where"):
        w = q.where
        if w is not None and hasattr(w, "connector") and hasattr(w, "children"):
            conn = w.connector
            children = w.children
            if conn == "AND" and children is not None and len(children) == 2:
                for exp in children:
                    if exp.lookup_name == "gte" or exp.lookup_name == "gt":
                        startdate, lower_bound_op = exp.rhs, exp.lookup_name
                    if exp.lookup_name == "lte" or exp.lookup_name == "lt":
                        enddate, upper_bound_op = exp.rhs, exp.lookup_name

    return startdate, lower_bound_op, enddate, upper_bound_op


def gen_ctx_grpby_datefld(
    request,
    response,
    uniq_fld_name,
    filters,
    date_fld_name,
    clazz_model,
    date_hierarchy,
):

    period = get_next_in_date_hierarchy(
        request,
        date_hierarchy,
    )

    startdate, lower_bound_op, enddate, upper_bound_op = extract_date_range(response)
    dt_range = None
    if startdate and lower_bound_op and enddate and upper_bound_op:
        dt_range = {
            "{}__{}".format(date_fld_name, lower_bound_op): startdate,
            "{}__{}".format(date_fld_name, upper_bound_op): enddate,
        }

    aggregate_by_period_ctx = {}
    aggregate_by_period_ctx["period"] = period

    total_by_date = None
    q_filter = filters if filters is not None else None
    if dt_range:
        if q_filter:
            q_filter = {**q_filter, **dt_range}
        else:
            q_filter = dt_range
    if q_filter is not None:
        total_by_date = (
            clazz_model.objects.filter(**q_filter)
            .annotate(
                period=Trunc(
                    date_fld_name,
                    period,
                    output_field=DateTimeField(),
                ),
            )
            .values("period")
            .annotate(sub_total=Count(uniq_fld_name))
            .order_by("period")
        )
    else:
        total_by_date = (
            clazz_model.objects.all()
            .annotate(
                period=Trunc(
                    date_fld_name,
                    period,
                    output_field=DateTimeField(),
                ),
            )
            .values("period")
            .annotate(sub_total=Count(uniq_fld_name))
            .order_by("period")
        )

    sub_totals_range = total_by_date.aggregate(
        low=Min("sub_total"),
        high=Max("sub_total"),
    )

    high = sub_totals_range.get("high", 0)
    low = sub_totals_range.get("low", 0)
    chart_list = []
    for e in total_by_date:
        chart_list.append(
            {
                "period": e["period"],
                "sub_total": e["sub_total"] or 0,
                "pct": (e["sub_total"] or 0) / high * 100 if high > low else 0,
            }
        )
    return chart_list


def gen_ctx_grp_by_flds(
    clazz_model, grp_flds, uniq_fld, marked_fld_name, marked_fld_val
):
    row_cnts_grp_by = (
        clazz_model.objects.all()
        .values(*grp_flds)
        .annotate(row_cnt=Count(uniq_fld))
        .order_by("row_cnt")
    )

    row_cnts_range = row_cnts_grp_by.aggregate(
        low=Min("row_cnt"),
        high=Max("row_cnt"),
    )

    high = row_cnts_range.get("high", 0)
    low = row_cnts_range.get("low", 0)
    chart_data_list = []
    for x in row_cnts_grp_by:
        item = {
            "row_cnt": x["row_cnt"] or 0,
            "pct": (x["row_cnt"] or 0) / high * 100 if high > low else 0,
        }
        if x[marked_fld_name] == marked_fld_val:
            item["marked"] = True
        grp_by_item = {}
        for y in grp_flds:
            grp_by_item[y] = x[y]
        item.update(grp_by_item)
        chart_data_list.append(item)
    return chart_data_list


def get_next_in_date_hierarchy(request, date_hierarchy):
    if date_hierarchy + "__day" in request.GET:
        return "hour"
    if date_hierarchy + "__month" in request.GET:
        return "day"
    if date_hierarchy + "__year" in request.GET:
        return "week"
    return "month"


def get_my_tokens_widget(u, id):
    widget_html = "<div><ul>"
    for v in TOKEN_VIEWERS:
        widget_html += "<li>"
        widget_html += LINK_REF_FMT.format(
            BB2_TOOLS_PATH,
            v.__name__.lower(),
            u,
            id,
            str(v()._meta.verbose_name_plural),
        )
        widget_html += "</li>"

    widget_html += "</ul></div>"
    return widget_html


class ReadOnlyAdmin(admin.ModelAdmin):
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        return (
            list(self.readonly_fields)
            + [field.name for field in obj._meta.fields]
            + [field.name for field in obj._meta.many_to_many]
        )

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
        token_cnts_by_app = (
            clazz_model.objects.all()
            .values("application__name")
            .annotate(tk_cnt=Count("token"))
            .order_by("application__name")
        )

        token_total = clazz_model.objects.all().count()

        response.context_data["token_total"] = token_total

        token_cnts_range = token_cnts_by_app.aggregate(
            low=Min("tk_cnt"),
            high=Max("tk_cnt"),
        )

        high = token_cnts_range.get("high", 0)
        low = token_cnts_range.get("low", 0)

        token_no_demo_dict = {}
        token_no_demo_total = 0
        chart_list = []
        table_list = []
        if clazz_model == AccessToken or clazz_model == ArchivedToken:
            # aggregations for access token and archived token only - without demographic scopes
            token_no_demo_cnts_by_app = (
                clazz_model.objects.filter(~Q(scope__icontains="patient/Patient.read"))
                .values("application__name")
                .annotate(tk_cnt=Count("token"))
                .order_by("application__name")
            )
            token_no_demo_total = clazz_model.objects.filter(
                ~Q(scope__icontains="patient/Patient.read")
            ).count()
            response.context_data["token_no_demo_total"] = token_no_demo_total
            for t in token_no_demo_cnts_by_app:
                token_no_demo_dict[t["application__name"]] = t["tk_cnt"]
            response.context_data["has_demo_scope_cnts"] = True
            for x in token_cnts_by_app:
                no_demo_cnt = token_no_demo_dict.get(x["application__name"])
                demo_cnt = x["tk_cnt"] - (0 if no_demo_cnt is None else no_demo_cnt)
                table_list.append(
                    {
                        "application__name": x["application__name"],
                        "tk_cnt": x["tk_cnt"] or 0,
                        "no_demo_tk_cnt": no_demo_cnt or 0,
                    }
                )
                chart_list.append(
                    {
                        "application__name": x["application__name"],
                        "tk_cnt": x["tk_cnt"] or 0,
                        "no_demo_tk_cnt": no_demo_cnt or 0,
                        "no_demo_pct": (no_demo_cnt or 0) / high * 100
                        if high > low
                        else 0,
                        "pct": (demo_cnt or 0) / high * 100 if high > low else 0,
                    }
                )
        else:
            response.context_data["has_demo_scope_cnts"] = False
            for x in token_cnts_by_app:
                table_list.append(
                    {
                        "application__name": x["application__name"],
                        "tk_cnt": x["tk_cnt"] or 0,
                    }
                )
                chart_list.append(
                    {
                        "application__name": x["application__name"],
                        "tk_cnt": x["tk_cnt"] or 0,
                        "pct": (x["tk_cnt"] or 0) / high * 100 if high > low else 0,
                    }
                )

        response.context_data["token_cnts_by_apps"] = table_list
        response.context_data["token_cnts_by_app_chart"] = chart_list

        return response


@admin.register(BeneficiaryDashboard)
class BeneficiaryDashboardAdmin(ReadOnlyAdmin):
    change_form_template = "admin/bb2_bene_dashboard_change_form.html"
    list_display = (
        "get_user_username",
        "get_identities",
        "get_access_tokens",
        "get_connected_applications",
        "date_created",
    )
    search_fields = ('user__username', 'fhir_id_v2', 'fhir_id_v3', '_user_id_hash', '_user_mbi')
    readonly_fields = ('date_created',)
    raw_id_fields = ('user',)

    def get_queryset(self, request):
        qs = super(BeneficiaryDashboardAdmin, self).get_queryset(request)
        return qs

    @admin.display(
        description="User Name",
        ordering="username",
    )
    def get_user_username(self, obj):
        return obj.user.username

    @admin.display(
        description="My Tokens",
        ordering="MyTokens",
    )
    def get_access_tokens(self, obj):
        # use relative URI in ref link to avoid re-login
        return format_html(get_my_tokens_widget(obj.user.username, obj.user.id))

    @admin.display(
        description="My Identities",
        ordering="MyIdentities",
    )
    def get_identities(self, obj):
        return format_html(
            '<div><ul><li>FHIR_ID_V2:{}</li><li>FHIR_ID_V3:{}</li><li>HICN HASH:{}</li><li>MBI:{}</li>'.format(
                obj.fhir_id(2), obj.fhir_id(3), obj.user_hicn_hash, obj.user_mbi
            )
        )

    @admin.display(
        description="My Connected Apps",
        ordering="MyConnectedApps",
    )
    def get_connected_applications(self, obj):
        inlinehtml = "<div><ul>"
        tokens = (
            MyAccessTokenViewer.objects.filter(user=obj.user_id)
            .values("user", "application")
            .annotate(token_count=Count("token"))
        )
        for t in tokens:
            app = get_application_model().objects.get(id=t["application"])
            inlinehtml += "<li>App:{}, Token Count:{}</li>".format(
                app.name, t["token_count"]
            )

        refreshtokens = (
            MyRefreshTokenViewer.objects.filter(user=obj.user_id)
            .values("user", "application")
            .annotate(token_count=Count("token"))
        )
        for t in refreshtokens:
            app = get_application_model().objects.get(id=t["application"])
            inlinehtml += "<li>App:{}, Refresh Token Count:{}</li>".format(
                app.name, t["token_count"]
            )

        archivedtokens = (
            MyArchivedTokenViewer.objects.filter(user=obj.user_id)
            .values("user", "application")
            .annotate(token_count=Count("token"))
        )
        for t in archivedtokens:
            app = get_application_model().objects.get(id=t["application"])
            inlinehtml += "<li>App:{}, Archived Token Count:{}</li>".format(
                app.name, t["token_count"]
            )

        inlinehtml += "</ul></div>"

        return format_html(inlinehtml)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        crosswalk = BeneficiaryDashboard.objects.get(pk=int(object_id))

        json_resp = None
        try:
            # DEPRECATE_V2: If we ever deprecate v2, this function and call need to be updated
            json_resp = get_v2_patient_by_id(crosswalk.fhir_id(2), request)
        except Exception as e:
            json_resp = {"backend_error": str(e)}

        extra_context["warning_label"] = {
            "pii_warning_text": (
                "This page might contain sensitive"
                " identity information when deployed in production, "
                "and is only for personnel with access permission."
            )
        }
        extra_context["info_from_bfd"] = json.dumps(json_resp, sort_keys=True, indent=4)
        return super(BeneficiaryDashboardAdmin, self).change_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )


@admin.register(MyAccessTokenViewer)
class MyAccessTokenViewerAdmin(ReadOnlyAdmin):
    list_display = (
        "user",
        "application",
        "expires",
        "scope",
        "token",
        "updated",
        "created",
        "get_source_refresh_token",
    )
    search_fields = (
        "user__username__exact",
        "application__name",
        "token",
        "source_refresh_token__token",
    )
    raw_id_fields = ("user", "application", "source_refresh_token")

    @admin.display(
        description="Source Refresh Token",
        ordering="token",
    )
    def get_source_refresh_token(self, obj):
        return obj.source_refresh_token.token if obj.source_refresh_token else None


@admin.register(MyRefreshTokenViewer)
class MyRefreshTokenViewerAdmin(ReadOnlyAdmin):
    list_display = (
        "user",
        "application",
        "token",
        "access_token_id",
        "revoked",
        "updated",
        "created",
    )
    search_fields = ("user__username__exact", "application__name", "token")
    raw_id_fields = ("user", "application")


@admin.register(MyArchivedTokenViewer)
class MyArchivedTokenViewerAdmin(ReadOnlyAdmin):
    list_display = (
        "user",
        "application",
        "expires",
        "scope",
        "token",
        "archived_at",
        "updated",
        "created",
    )
    search_fields = ("user__username", "application__name", "token")
    raw_id_fields = ("user", "application")


@admin.register(DummyAdminObject)
class BlueButtonAPISplunkLauncherAdmin(ReadOnlyAdmin):
    change_list_template = "admin/bb2_splunk_dashboards_change_list.html"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )
        response.context_data["splunk_dashboards"] = settings.SPLUNK_DASHBOARDS
        return response


@admin.register(ApplicationStats)
class ApplicationStatsAdmin(ReadOnlyAdmin):
    change_list_template = "admin/apps_stats_change_list.html"
    list_display = (
        "name",
        "user",
        "authorization_grant_type",
        "client_id",
        "require_demographic_scopes",
        "scopes",
        "created",
        "updated",
        "skip_authorization",
    )
    radio_fields = {
        "client_type": admin.HORIZONTAL,
        "authorization_grant_type": admin.VERTICAL,
    }

    date_hierarchy = "created"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        clazz_model = ApplicationStats
        total = clazz_model.objects.all().count()
        panels = []

        # apps counts over signed up time as bar chart
        app_grp_by_created_date_ctx = gen_ctx_grpby_datefld(
            request, response, "name", None, "created", clazz_model, self.date_hierarchy
        )
        top_panel = {
            "type": "bar-chart",
            "title": "Apps Count by Signup Date, Total ({})".format(total),
            "body": app_grp_by_created_date_ctx,
        }

        # bar chart top: apps count by sign up date
        # bar chart 2nd row left: apps count group be active field
        # bar chart 2nd row center: apps opt in demo info vs apps opt out of demo info
        # bar chart 2nd row right: apps counts group be grant_type + client_type
        # table view bottom: apps count by sign up date
        panels.append(top_panel)
        center_panel = []
        center_panel.append(
            {
                "body": gen_ctx_grp_by_flds(
                    clazz_model, ["active"], "name", "active", False
                ),
                "tooltip_txt": ["active = False", "active = True"],
                "title": "Apps Count by Active Flag",
            }
        )

        center_panel.append(
            {
                "body": gen_ctx_grp_by_flds(
                    clazz_model,
                    ["require_demographic_scopes"],
                    "name",
                    "require_demographic_scopes",
                    False,
                ),
                "tooltip_txt": [
                    "require_demographic_scopes = False",
                    "require_demographic_scopes = True",
                ],
                "title": "Apps Count by Demographic Choice",
            }
        )

        center_panel.append(
            {
                "body": gen_ctx_grp_by_flds(
                    clazz_model,
                    ["client_type", "authorization_grant_type"],
                    "name",
                    "client_type",
                    "public",
                ),
                "tooltip_txt": ["client_type = public", "client type is not public"],
                "title": "Apps Count by Client & Grant Type",
            }
        )

        panels.append({"type": "horiz-charts", "data": center_panel})

        bottom_panel = {
            "type": "table-view",
            "title": "Apps Count by Signup Date, Total ({})".format(total),
            "header": ["Period", "Apps Count", "Percentage"],
            "body": app_grp_by_created_date_ctx,
            "total": total,
            "footer": ["Total", total, "100%"],
        }

        panels.append(bottom_panel)
        response.context_data["panels"] = panels

        return response


@admin.register(UserStats)
class UserCountByCreateDateAdmin(ReadOnlyAdmin):
    change_list_template = "admin/user_counts_by_date_change_list.html"
    date_hierarchy = "user__date_joined"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        clazz_model = UserProfile
        total = clazz_model.objects.all().count()
        total_dev = clazz_model.objects.all().filter(user_type="DEV").count()
        total_ben = clazz_model.objects.all().filter(user_type="BEN").count()
        panels = []

        ben_user_grp_by_created_date_ctx = gen_ctx_grpby_datefld(
            request,
            response,
            "id",
            {"user_type": "BEN"},
            "user__date_joined",
            clazz_model,
            self.date_hierarchy,
        )
        top_panel = {
            "type": "bar-chart",
            "title": (
                "Beneficiaries Counts by Joined Date, "
                'User Total: {}, "BEN": {}, "DEV": {}'
            ).format(total, total_ben, total_dev),
            "highlight": "no",
            "body": ben_user_grp_by_created_date_ctx,
        }

        panels.append(top_panel)

        dev_user_grp_by_created_date_ctx = gen_ctx_grpby_datefld(
            request,
            response,
            "id",
            {"user_type": "DEV"},
            "user__date_joined",
            clazz_model,
            self.date_hierarchy,
        )
        center_panel = {
            "type": "bar-chart",
            "title": (
                "Developer User Counts by Joined Date:"
                ' User Total: {}, "BEN": {}, "DEV": {}'
            ).format(total, total_ben, total_dev),
            "highlight": "yes",
            "body": dev_user_grp_by_created_date_ctx,
        }

        panels.append(center_panel)

        dev_user_list = (
            clazz_model.objects.filter(user_type="DEV")
            .values(
                "user__username",
                "user__first_name",
                "user__last_name",
                "organization_name",
                "user_type",
                "user__is_superuser",
                "user__is_staff",
                "user__is_active",
                "user__last_login",
                "user__date_joined",
            )
            .order_by("user__date_joined")
        )

        bottom_panel = {
            "type": "flat-table-view",
            "title": "DEV User List (Total: {})".format(total_dev),
            "header": [
                "Name",
                "Fist Name",
                "Last Name",
                "Organization",
                "User Type",
                "Is SuperUser",
                "Is Staff",
                "Is Active",
                "Last Login",
                "Date Joined",
            ],
            "body": list(dev_user_list),
        }

        panels.append(bottom_panel)
        response.context_data["panels"] = panels

        return response


@admin.register(AccessTokenStats)
class ConnectedBeneficiaryCountByAppsAdmin(TokenCountByAppsAdmin):
    change_list_template = "admin/token_counts_by_apps_change_list.html"
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
            "bar_chart_title": "Access Token Count by Apps, Total ({})".format(
                response.context_data["token_total"]
            ),
            "bar_chart_no_demo_title": (
                "Access Token Count" " (No Demo Scope) by Apps, Total ({})"
            ).format(response.context_data["token_total"]),
            "table_view_title": "Access Token Count by Apps, Total ({})".format(
                response.context_data["token_total"]
            ),
        }
        return response


@admin.register(RefreshTokenStats)
class RefreshTokenCountByAppsAdmin(TokenCountByAppsAdmin):
    change_list_template = "admin/token_counts_by_apps_change_list.html"

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
            "bar_chart_title": "Refresh Token Count by Apps, Total ({})".format(
                response.context_data["token_total"]
            ),
            "table_view_title": "Refresh Token Count by Apps, Total ({})".format(
                response.context_data["token_total"]
            ),
        }
        return response


@admin.register(ArchivedTokenStats)
class ArchivedTokenStatsAdmin(TokenCountByAppsAdmin):
    change_list_template = "admin/token_counts_by_apps_change_list.html"

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
            "bar_chart_title": "Archived Token Count by Apps, Total ({})".format(
                response.context_data["token_total"]
            ),
            "table_view_title": "Archived Token Count by Apps, Total ({})".format(
                response.context_data["token_total"]
            ),
        }
        return response


class UserTypeFilter(admin.SimpleListFilter):
    title = "User type"
    parameter_name = "userprofile__type"

    def lookups(self, request, model_admin):
        return [
            ("BEN", "Beneficiary"),
            ("DEV", "Developer"),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(userprofile__user_type=self.value())
        return queryset
