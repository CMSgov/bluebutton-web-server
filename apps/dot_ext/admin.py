from django.contrib import admin
from django.forms import ModelForm
from oauth2_provider.models import AccessToken
from oauth2_provider.models import get_application_model
from .models import ApplicationLabel
from .forms import CustomRegisterApplicationForm


Application = get_application_model()


class MyAccessToken(AccessToken):

    class Meta:
        proxy = True
        app_label = "bluebutton"


class MyApplication(Application):

    class Meta:
        proxy = True
        app_label = "bluebutton"


class CustomAdminApplicationForm(CustomRegisterApplicationForm):

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)

    class Meta:
        model = MyApplication
        fields = (
            'client_id',
            'user',
            'client_type',
            'authorization_grant_type',
            'client_secret',
            'name',
            'skip_authorization',
            'scope',
            'agree',
            'op_tos_uri',
            'op_policy_uri',
            'client_uri',
            'website_uri',
            'redirect_uris',
            'logo_uri',
            'logo_image',
            'tos_uri',
            'policy_uri',
            'software_id',
            'contacts',
            'support_email',
            'support_phone_number',
            'description',
            'active',
            'first_active',
            'last_active',
        )

    def clean(self):
        return self.cleaned_data

    def clean_name(self):
        return super().clean_name()

    def clean_agree(self):
        return self.cleaned_data.get('agree')

    def clean_redirect_uris(self):
        return self.cleaned_data.get('redirect_uris')

    def clean_logo_image(self):
        return super().clean_logo_image()

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class MyApplicationAdmin(admin.ModelAdmin):

    form = CustomAdminApplicationForm
    list_display = ("name", "user", "authorization_grant_type", "client_id",
                    "skip_authorization", "scopes", "created", "updated")
    list_filter = ("name", "user", "client_type", "authorization_grant_type",
                   "skip_authorization")
    radio_fields = {
        "client_type": admin.HORIZONTAL,
        "authorization_grant_type": admin.VERTICAL,
    }
    raw_id_fields = ("user", )


admin.site.register(MyApplication, MyApplicationAdmin)


class MyAccessTokenAdmin(admin.ModelAdmin):

    list_display = ('user', 'application', 'expires', 'scope')
    search_fields = ('user__username', 'application__name',)
    list_filter = ("user", "application")
    raw_id_fields = ("user", 'application')


admin.site.register(MyAccessToken, MyAccessTokenAdmin)


class ApplicationLabelAdmin(admin.ModelAdmin):
    model = ApplicationLabel
    filter_horizontal = ('applications',)
    list_display = ("name", "slug", "short_description")
    list_filter = ("name", "slug")


admin.site.register(ApplicationLabel, ApplicationLabelAdmin)
