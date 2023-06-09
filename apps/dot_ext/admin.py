from django import forms
from django.contrib import admin
from oauth2_provider.models import AccessToken
from oauth2_provider.models import get_application_model
from .forms import CreateNewApplicationForm, CustomRegisterApplicationForm
from .models import ApplicationLabel, AuthFlowUuid
from .utils import is_data_access_type_valid

Application = get_application_model()


class MyAccessToken(AccessToken):
    class Meta:
        proxy = True
        app_label = "bluebutton"


class MyApplication(Application):
    class Meta:
        proxy = True
        app_label = "bluebutton"


class MyAuthFlowUuid(AuthFlowUuid):
    class Meta:
        proxy = True
        app_label = "bluebutton"


class CreateNewApplication(Application):
    class Meta:
        proxy = True
        app_label = "bluebutton"


class CustomAdminApplicationForm(CustomRegisterApplicationForm):
    description = forms.CharField(
        label="Application Description",
        help_text="Note text size and HTML tags are not validated under ADMIN.",
        widget=forms.Textarea,
        empty_value="",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        user = None
        super().__init__(user, *args, **kwargs)
        self.fields["logo_uri"].widget.attrs["readonly"] = False

    class Meta:
        model = MyApplication
        fields = (
            "data_access_type",
            "end_date",
            "client_id",
            "user",
            "client_type",
            "authorization_grant_type",
            "client_secret_plain",
            "client_secret",
            "name",
            "skip_authorization",
            "scope",
            "require_demographic_scopes",
            "agree",
            "op_tos_uri",
            "op_policy_uri",
            "client_uri",
            "website_uri",
            "redirect_uris",
            "logo_uri",
            "logo_image",
            "tos_uri",
            "policy_uri",
            "software_id",
            "contacts",
            "support_email",
            "support_phone_number",
            "description",
            "active",
            "first_active",
            "last_active",
        )

    def clean(self):
        # Validate data access type and end_date
        data_access_type = self.cleaned_data.get("data_access_type")
        end_date = self.cleaned_data.get("end_date")
        user = self.cleaned_data.get("user")

        is_valid, mesg = is_data_access_type_valid(user, data_access_type, end_date)

        if not is_valid:
            raise forms.ValidationError(mesg)

        return self.cleaned_data

    def clean_agree(self):
        return self.cleaned_data.get("agree")


@admin.register(MyApplication)
class MyApplicationAdmin(admin.ModelAdmin):
    form = CustomAdminApplicationForm
    list_display = (
        "name",
        "get_data_access_type",
        "get_end_date",
        "user",
        "client_id",
        "require_demographic_scopes",
        "scopes",
        "created",
        "updated",
        "active",
        "skip_authorization",
    )
    list_filter = (
        "data_access_type",
        "end_date",
        "require_demographic_scopes",
        "active",
        "skip_authorization",
    )
    radio_fields = {
        "client_type": admin.HORIZONTAL,
        "authorization_grant_type": admin.VERTICAL,
    }

    search_fields = (
        "name",
        "data_access_type",
        "user__username",
        "=client_id",
        "=require_demographic_scopes",
        "=authorization_grant_type",
    )

    raw_id_fields = ("user",)

    def get_data_access_type(self, obj):
        return obj.data_access_type
    get_data_access_type.short_description = "Data Access Type"

    def get_end_date(self, obj):
        return obj.end_date
    get_end_date.short_description = "Data Access End Date"


@admin.register(CreateNewApplication)
class CreateNewApplicationAdmin(admin.ModelAdmin):
    form = CreateNewApplicationForm
    list_display = (
        "name",
        "user",
        "client_id",
        "created",
        "updated",
        "active",
        "skip_authorization",
    )
    list_filter = (
        "client_type",
        "active",
        "skip_authorization",
    )

    search_fields = (
        "name",
        "user__username",
        "=client_id",
    )

    raw_id_fields = ("user",)


@admin.register(MyAccessToken)
class MyAccessTokenAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "application",
        "expires",
        "scope",
        "token",
        "get_source_refresh_token",
    )
    search_fields = (
        "user__username",
        "application__name",
        "token",
        "source_refresh_token__token",
    )
    raw_id_fields = ("user", "application", "source_refresh_token")

    def get_source_refresh_token(self, obj):
        return obj.source_refresh_token.token if obj.source_refresh_token else None

    get_source_refresh_token.admin_order_field = "token"
    get_source_refresh_token.short_description = "Source Refresh Token"


@admin.register(MyAuthFlowUuid)
class MyAuthFlowUuidAdmin(admin.ModelAdmin):
    list_display = (
        "created",
        "auth_uuid",
        "state",
        "code",
        "client_id",
        "auth_pkce_method",
        "auth_crosswalk_action",
        "auth_share_demographic_scopes",
    )
    search_fields = ("auth_uuid", "state", "code")


@admin.register(ApplicationLabel)
class ApplicationLabelAdmin(admin.ModelAdmin):
    model = ApplicationLabel
    filter_horizontal = ("applications",)
    list_display = ("name", "slug", "short_description")
    list_filter = ("name", "slug")
