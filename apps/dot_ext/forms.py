import logging
import uuid

from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from oauth2_provider.forms import AllowForm as DotAllowForm
from oauth2_provider.models import get_application_model
from apps.accounts.models import UserProfile
from apps.capabilities.models import ProtectedCapability
from apps.dot_ext.models import Application, InternalApplicationLabels
from apps.dot_ext.validators import validate_logo_image, validate_notags
from django.contrib.auth.models import Group, User
from waffle import switch_is_active

import apps.logging.request_logger as bb2logging

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))

PRINTABLE_SPECIAL_ASCII = "!\"#$%&'()*+,-/:;<=>?@[\\]^_`{|}~"

# TODO Consider refactoring the following two forms which are possibly redundant
# Refer to comment on BB2-2933


class CustomRegisterApplicationForm(forms.ModelForm):
    logo_image = forms.ImageField(
        label="Logo URI Image Upload",
        required=False,
        help_text="Upload your logo image file here in JPEG (.jpg) format! "
        "The maximum file size allowed is %sKB and maximum dimensions are %sx%s pixels. "
        "This will update the Logo URI after saving."
        % (
            settings.APP_LOGO_SIZE_MAX,
            settings.APP_LOGO_WIDTH_MAX,
            settings.APP_LOGO_HEIGHT_MAX,
        ),
    )

    description = forms.CharField(
        label="Application Description",
        help_text="This is plain-text up to 1000 characters in length.",
        widget=forms.Textarea,
        empty_value="",
        required=False,
        max_length=1000,
        validators=[validate_notags],
    )

    def __init__(self, user, *args, **kwargs):
        agree_label = (
            'Yes I have read and agree to the <a target="_blank" href="%s">API Terms of Service Agreement</a>*'
            % (settings.TOS_URI)
        )
        super(CustomRegisterApplicationForm, self).__init__(*args, **kwargs)
        self.fields["authorization_grant_type"].choices = settings.GRANT_TYPES
        self.fields["client_type"].initial = "confidential"
        self.fields["agree"].label = mark_safe(agree_label)
        self.fields["name"].label = "Name*"
        self.fields["name"].required = True
        self.fields["client_type"].label = "Client Type*"
        self.fields["client_type"].required = False
        self.fields["authorization_grant_type"].label = "Authorization Grant Type*"
        self.fields["authorization_grant_type"].required = False
        self.fields["redirect_uris"].label = "Redirect URIs*"
        self.fields["logo_uri"].disabled = True
        # form field 'internal_application_labels' made dynamic per switch
        if switch_is_active('enable_internal_application_labels'):
            self.fields['internal_application_labels'] = forms.ModelMultipleChoiceField(
                queryset=InternalApplicationLabels.objects.all(),
                widget=forms.SelectMultiple)
        else:
            if self.fields.pop("internal_application_labels", None) is not None:
                try:
                    del self.fields['internal_application_labels']
                except KeyError:
                    pass

    class Meta:
        model = get_application_model()
        fields = (
            "name",
            "client_type",
            "authorization_grant_type",
            "redirect_uris",
            "logo_uri",
            "logo_image",
            "website_uri",
            "description",
            "policy_uri",
            "tos_uri",
            "support_email",
            "support_phone_number",
            "contacts",
            "agree",
            "require_demographic_scopes",
        )

    required_css_class = "required"

    def clean(self):
        return self.cleaned_data

    def clean_name(self):
        name = self.cleaned_data.get("name")
        app_model = get_application_model()
        if (
            app_model.objects.filter(name__iexact=name)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(
                """
                                        It looks like this application name
                                        is already in use with another app.
                                        Please enter a different application
                                        name to prevent future errors.
                                        Note that names are case-insensitive.
                                        """
            )
        if not app_model.objects.filter(name__iexact=name).exists():
            # new app, restrict app name to only printable ASCII (32-127)
            if not (str(name).isprintable() and str(name).isascii()):
                raise forms.ValidationError(
                    """
                                            Invalid character(s) in application name ({}),
                                            Allowed characters:
                                            Alphanumeric characters 0 to 9, a to z, A to Z, space character,
                                            Special characters {}
                                            """.format(
                        name, PRINTABLE_SPECIAL_ASCII
                    )
                )
        return name

    def clean_agree(self):
        agree = self.cleaned_data.get("agree")
        if not agree:
            msg = _("You must agree to the API Terms of Service Agreement")
            raise forms.ValidationError(msg)
        return agree

    def clean_redirect_uris(self):
        redirect_uris = self.cleaned_data.get("redirect_uris")
        if getattr(settings, "BLOCK_HTTP_REDIRECT_URIS", True):
            if redirect_uris:
                for u in redirect_uris.split():
                    if u.startswith("http://"):
                        msg = _("Redirect URIs must not use http.")
                        raise forms.ValidationError(msg)
        return redirect_uris

    def clean_logo_image(self):
        logo_image = self.cleaned_data.get("logo_image")
        if getattr(logo_image, "name", False):
            validate_logo_image(logo_image)
        return logo_image

    def clean_require_demographic_scopes(self):
        require_demographic_scopes = self.cleaned_data.get("require_demographic_scopes")
        if not isinstance(require_demographic_scopes, bool):
            msg = _(
                "Does your application need to collect beneficiary demographic information must be (Yes/No)."
            )
            raise forms.ValidationError(msg)
        return require_demographic_scopes

    def save(self, *args, **kwargs):
        self.instance.client_type = "confidential"
        self.instance.authorization_grant_type = "authorization-code"
        app = self.instance
        # Only log agreement from a Register form
        if app.agree and isinstance(self, CustomRegisterApplicationForm):
            logmsg = "%s agreed to %s for the application %s" % (
                app.user,
                app.op_tos_uri,
                app.name,
            )
            logger.info(logmsg)
        app = super().save(*args, **kwargs)
        app.save()
        uri = app.store_media_file(
            self.cleaned_data.pop("logo_image", None), "logo.jpg"
        )
        if uri:
            app.logo_uri = uri
            app.save()
        return app


class CreateNewApplicationForm(forms.ModelForm):
    logo_image = forms.ImageField(
        label="Logo URI Image Upload",
        required=False,
        help_text="Upload your logo image file here in JPEG (.jpg) format! "
        "The maximum file size allowed is %sKB and maximum dimensions are %sx%s pixels. "
        "This will update the Logo URI after saving."
        % (
            settings.APP_LOGO_SIZE_MAX,
            settings.APP_LOGO_WIDTH_MAX,
            settings.APP_LOGO_HEIGHT_MAX,
        ),
    )
    description = forms.CharField(
        label="Application Description",
        help_text="This is plain-text up to 1000 characters in length.",
        widget=forms.Textarea,
        empty_value="",
        required=False,
        max_length=1000,
        validators=[validate_notags],
    )
    organization_name = forms.CharField(required=True)

    class Meta:
        model = get_application_model()
        fields = (
            "name",
            "organization_name",
            "contacts",
            "redirect_uris",
            "require_demographic_scopes",
            "policy_uri",
            "tos_uri",
            "website_uri",
            "support_email",
            "support_phone_number",
            "logo_image",
            "description",
        )

    # Duplication of clean_name() from above form, see TODO comment at start of file
    # about candidate for refactoring
    def clean_name(self):

        name = self.cleaned_data.get("name")
        app_model = get_application_model()
        if (
            app_model.objects.filter(name__iexact=name)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(
                """
                                        It looks like this application name
                                        is already in use with another app.
                                        Please enter a different application
                                        name to prevent future errors.
                                        Note that names are case-insensitive.
                                        """
            )
        if not app_model.objects.filter(name__iexact=name).exists():
            # new app, restrict app name to only printable ASCII (32-127)
            if not (str(name).isprintable() and str(name).isascii()):
                raise forms.ValidationError(
                    """
                            Invalid character(s) in application name ({}),
                            Allowed characters:
                            Alphanumeric characters 0 to 9, a to z, A to Z, space character,
                            Special characters {}
                            """.format(
                        name, PRINTABLE_SPECIAL_ASCII
                    )
                )
        return name

    def clean_logo_image(self):

        logo_image = self.cleaned_data.get("logo_image")
        if getattr(logo_image, "name", False):
            validate_logo_image(logo_image)
        return logo_image

    def clean_redirect_uris(self):

        redirect_uris = self.cleaned_data.get("redirect_uris")
        if getattr(settings, "BLOCK_HTTP_REDIRECT_URIS", True):
            if redirect_uris:
                for u in redirect_uris.split():
                    if u.startswith("http://"):
                        msg = _("Redirect URIs must not use http.")
                        raise forms.ValidationError(msg)
        return redirect_uris

    def clean_require_demographic_scopes(self):

        require_demographic_scopes = self.cleaned_data.get("require_demographic_scopes")
        if not isinstance(require_demographic_scopes, bool):
            msg = _(
                "Does your application need to collect beneficiary demographic information must be (Yes/No)."
            )
            raise forms.ValidationError(msg)
        return require_demographic_scopes

    def save(self, *args, **kwargs):
        app = self.instance

        new_user_model = User.objects.create(
            username=self.cleaned_data.get("name") + "@example.com",
            password=str(uuid.uuid4()),
            is_active=True,
        )
        group = Group.objects.get(name="BlueButton")
        new_user_model.groups.add(group)
        new_user_model.save()

        UserProfile.objects.create(
            user=new_user_model,
            organization_name=self.cleaned_data.get("organization_name"),
        )

        app = super().save(*args, **kwargs)
        app.agree = True
        app.user = new_user_model
        app.authorization_grant_type = Application.GRANT_AUTHORIZATION_CODE
        app.client_type = Application.CLIENT_CONFIDENTIAL
        app.save()
        app.scope.add(
            *list(
                ProtectedCapability.objects.filter(default=True).values_list(
                    "id", flat=True
                )
            )
        )
        app.save()
        uri = app.store_media_file(
            self.cleaned_data.pop("logo_image", None), "logo.jpg"
        )
        if uri:
            app.logo_uri = uri
            app.save()
        return app


class SimpleAllowForm(DotAllowForm):
    code_challenge = forms.CharField(required=False, widget=forms.HiddenInput())
    code_challenge_method = forms.CharField(required=False, widget=forms.HiddenInput())
    share_demographic_scopes = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        scope = cleaned_data.get("scope", None)

        if scope is None:
            cleaned_data["scope"] = ""
            scope = ""

        # Remove demographic information scopes, if beneficiary is not sharing
        if cleaned_data.get("share_demographic_scopes") != "True":
            cleaned_data["scope"] = " ".join(
                [
                    s
                    for s in scope.split(" ")
                    if s not in settings.BENE_PERSONAL_INFO_SCOPES
                ]
            )

        return cleaned_data
