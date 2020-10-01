from django.contrib import admin
from apps.bb2_tools.models import BeneficiaryDashboard, MyAccessTokenViewer, MyRefreshTokenViewer, MyArchivedTokenViewer
from django.utils.html import format_html

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
    list_display = ('get_user_username', 'fhir_id', 'user_hicn_hash', 'user_mbi_hash', 'get_access_tokens', 'date_created')
    search_fields = ('user__username', '_fhir_id', '_user_id_hash', '_user_mbi_hash')
    # fields = ('get_user_username', 'fhir_id', 'user_hicn_hash', 'user_mbi_hash', 'access_tokens', 'date_created')
    readonly_fields = ('date_created',)
    raw_id_fields = ("user", )

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
