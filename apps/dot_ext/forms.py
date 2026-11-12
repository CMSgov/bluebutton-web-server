import logging
import uuid
from typing import override

import waffle
from django import forms
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.forms.widgets import URLInput
from django.utils.translation import gettext_lazy as _
from oauth2_provider.forms import AllowForm as DotAllowForm
from oauth2_provider.generators import generate_client_secret
from oauth2_provider.models import get_application_model

from apps.accounts.models import UserProfile
from apps.capabilities.models import ProtectedCapability
from apps.constants import HHS_SERVER_LOGNAME_FMT
from apps.dot_ext.constants import (
    BENE_PERSONAL_INFO_SCOPES,
    CLIENT_CREDENTIALS_SUPPORTED_TYPES,
    GENERATE_CLIENT_SECRET,
    NO_CHANGE,
    NO_CLIENT_SECRET,
    PRINTABLE_SPECIAL_ASCII,
)
from apps.dot_ext.models import Application, InternalApplicationLabels
from apps.dot_ext.scopes import CapabilitiesScopes
from apps.dot_ext.validators import validate_application_name, validate_logo_image, validate_notags, validate_url

logger = logging.getLogger(HHS_SERVER_LOGNAME_FMT.format(__name__))


class CustomRegisterApplicationForm(forms.ModelForm):
    logo_image = forms.ImageField(
        label='Logo URI Image Upload',
        required=False,
        help_text='Upload your logo image file here in JPG, JPEG, or PNG (.jpg, .jpeg, .png) format! '
        'The maximum file size allowed is %sKB and maximum dimensions are %sx%s pixels. '
        'This will update the Logo URI after saving.'
        % (
            settings.APP_LOGO_SIZE_MAX,
            settings.APP_LOGO_WIDTH_MAX,
            settings.APP_LOGO_HEIGHT_MAX,
        ),
    )

    description = forms.CharField(
        label='Application Description',
        help_text='This is plain-text up to 1000 characters in length.',
        widget=forms.Textarea,
        empty_value='',
        required=False,
        max_length=1000,
        validators=[validate_notags],
    )

    policy_uri = forms.CharField(
        required=False,
        max_length=512,
        validators=[validate_url],
        widget=URLInput,
    )

    tos_uri = forms.CharField(
        required=False,
        max_length=512,
        validators=[validate_url],
        widget=URLInput,
    )

    website_uri = forms.CharField(
        required=False,
        max_length=512,
        validators=[validate_url],
        widget=URLInput,
    )
    jwks_uri = forms.CharField(
        required=False,
        max_length=512,
        validators=[validate_url],
        widget=URLInput,
    )
    agree_label = (
        'Yes I have read and agree to the <a target="_blank" href="%s">API Terms of Service Agreement</a>*'
        % (settings.TOS_URI)
    )

    def __init__(self, user, *args, **kwargs):
        super(CustomRegisterApplicationForm, self).__init__(*args, **kwargs)
        self.fields['allowed_auth_type'].required = False

    class Meta:
        model = get_application_model()
        fields = (
            'name',
            'redirect_uris',
            'logo_image',
            'website_uri',
            'logo_uri',
            'description',
            'policy_uri',
            'tos_uri',
            'support_email',
            'support_phone_number',
            'jwks_uri',
            'contacts',
            'agree',
            'require_demographic_scopes',
            'allowed_auth_type',
        )

    required_css_class = 'required'

    def clean(self):

        if not waffle.switch_is_active('enable_jwt_sbx_settings'):
            if self.instance and self.instance.pk:
                # Use the existing value already saved in the database
                self.cleaned_data['allowed_auth_type'] = self.instance.allowed_auth_type
                self.cleaned_data['jwks_uri'] = self.instance.jwks_uri
            else:
                # Defaults for a new application if the fields are not present in the form data
                self.cleaned_data['allowed_auth_type'] = 'AUTH_CODE'
                self.cleaned_data['jwks_uri'] = None

        allowed_auth_type = self.cleaned_data.get('allowed_auth_type')
        jwks_uri = self.cleaned_data.get('jwks_uri')

        # Ensure that jwks_uri is not null when allowed_auth_type is 'client_credentials' or 'both'
        if allowed_auth_type in CLIENT_CREDENTIALS_SUPPORTED_TYPES and not jwks_uri:
            raise forms.ValidationError(
                "The jwks_uri cannot be empty when allowed_auth_type is 'client_credentials' or 'both'."
            )

        return self.cleaned_data

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError(_('Application name is required.'))
        validate_application_name(name)
        app_model = get_application_model()
        if app_model.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
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
                                            """.format(name, PRINTABLE_SPECIAL_ASCII)
                )
        return name

    def clean_agree(self):
        agree = self.cleaned_data.get('agree')
        if not agree:
            msg = _('You must agree to the API Terms of Service Agreement')
            raise forms.ValidationError(msg)
        return agree

    def clean_redirect_uris(self):
        redirect_uris = self.cleaned_data.get('redirect_uris')
        if getattr(settings, 'BLOCK_HTTP_REDIRECT_URIS', True):
            if redirect_uris:
                for u in redirect_uris.split():
                    if u.startswith('http://'):
                        msg = _('Redirect URIs must not use http.')
                        raise forms.ValidationError(msg)
        return redirect_uris

    def clean_logo_image(self):
        logo_image = self.cleaned_data.get('logo_image')
        if getattr(logo_image, 'name', False):
            validate_logo_image(logo_image)
        return logo_image

    def clean_require_demographic_scopes(self):
        require_demographic_scopes = self.cleaned_data.get('require_demographic_scopes')
        if not isinstance(require_demographic_scopes, bool):
            msg = _('Does your application need to collect beneficiary demographic information must be (Yes/No).')
            raise forms.ValidationError(msg)
        return require_demographic_scopes

    def save(self, *args, **kwargs):
        app = self.instance
        app.client_type = Application.CLIENT_CONFIDENTIAL
        app.authorization_grant_type = Application.GRANT_AUTHORIZATION_CODE
        # Only log agreement from a Register form
        if app.agree and isinstance(self, CustomRegisterApplicationForm):
            logmsg = '%s agreed to %s for the application %s' % (
                app.user,
                app.op_tos_uri,
                app.name,
            )
            logger.info(logmsg)
        app = super().save(*args, **kwargs)

        default_scopes = ProtectedCapability.objects.filter(default__exact=True)
        demographic_scopes = ProtectedCapability.objects.filter(slug__in=BENE_PERSONAL_INFO_SCOPES)
        default_non_demographic = default_scopes.difference(demographic_scopes)

        if app.require_demographic_scopes:
            app.scope.add(*default_scopes)
        else:  # False or None
            app.scope.add(*default_non_demographic)
            app.scope.remove(*demographic_scopes)

        uri = app.store_media_file(self.cleaned_data.pop('logo_image', None))
        if uri:
            app.logo_uri = uri
            app.save()
        return app


class CreateApplicationForm(CustomRegisterApplicationForm):
    # Needed for user profile creation, but not part of the Application model
    organization_name = forms.CharField(required=True)
    # Add a user_mode field to the form to allow the developers to choose
    # between creating a new user or selecting an existing user
    USER_CHOICES = [
        ('existing', 'Choose Existing User'),
        ('new', 'Create New User'),
    ]
    user_mode = forms.ChoiceField(choices=USER_CHOICES, widget=forms.RadioSelect, initial='new', required=True)

    CLIENT_SECRET_ACTION_CHOICES = [
        (GENERATE_CLIENT_SECRET, 'Generate a client secret'),
        (NO_CLIENT_SECRET, 'Do not generate a client secret'),
    ]
    client_secret_action = forms.ChoiceField(
        choices=CLIENT_SECRET_ACTION_CHOICES, initial=GENERATE_CLIENT_SECRET, required=True
    )

    def __init__(self, *args, **kwargs):
        user = None
        super().__init__(user, *args, **kwargs)
        # Hide agree field and don't make it required since we handle later it in the save function
        self.fields['agree'].widget = forms.HiddenInput()
        self.fields['agree'].required = False
        self.fields['organization_name'].label = 'Organization Name*'
        self.fields['name'].label = 'Name*'
        self.fields['name'].required = True
        self.fields['user_mode'].label = 'User Mode*'
        self.fields['scope'].label = 'Scopes*'
        self.fields['allowed_auth_type'].label = 'Allowed Auth Type*'
        self.fields['client_secret_action'].label = 'Client Secret Action*'
        self.fields['internal_application_labels'] = forms.ModelMultipleChoiceField(
            queryset=InternalApplicationLabels.objects.all(), widget=forms.SelectMultiple
        )
        self.fields['internal_application_labels'].required = False
        self.fields['require_demographic_scopes'].label = 'Are Demographic Scopes Required?*'
        self.fields['require_demographic_scopes'].required = True

    class Meta:
        model = get_application_model()
        fields = (
            'data_access_type',
            'name',
            'client_secret_action',
            'user_mode',
            'user',
            'organization_name',
            'contacts',
            'agree',
            'redirect_uris',
            'require_demographic_scopes',
            'scope',
            'policy_uri',
            'tos_uri',
            'website_uri',
            'support_email',
            'support_phone_number',
            'logo_image',
            'description',
            'internal_application_labels',
            'jwks_uri',
            'allowed_auth_type',
            'part_d_eob_only',
        )

    @override
    def clean(self):
        if 'user_mode' in self.cleaned_data and 'user' in self.cleaned_data:
            user_mode = self.cleaned_data.get('user_mode')
            user = self.cleaned_data.get('user')
            # Validate that the user field is filled out correctly based on the user_mode selection
            if user_mode == 'existing' and not user:
                raise forms.ValidationError(
                    'You must select an existing user when choosing the "Choose Existing User" option.'
                )
            elif user_mode == 'new' and user:
                raise forms.ValidationError('You cannot select a user when choosing the "Create New User" option.')

        if 'jwks_uri' and 'client_secret_action' in self.cleaned_data:
            jwks_uri = self.cleaned_data.get('jwks_uri')
            client_secret_action = self.cleaned_data.get('client_secret_action')
            if not jwks_uri and client_secret_action == NO_CLIENT_SECRET:
                raise forms.ValidationError(
                    f'The jwks_uri cannot be empty when client_secret_action is {NO_CLIENT_SECRET}.'
                )

        if 'allowed_auth_type' in self.cleaned_data and 'jwks_uri' in self.cleaned_data:
            allowed_auth_type = self.cleaned_data.get('allowed_auth_type')
            jwks_uri = self.cleaned_data.get('jwks_uri')
            # Ensure that jwks_uri is not null when allowed_auth_type is 'client_credentials' or 'both'
            if allowed_auth_type in CLIENT_CREDENTIALS_SUPPORTED_TYPES and not jwks_uri:
                raise forms.ValidationError(
                    "The jwks_uri cannot be empty when allowed_auth_type is 'client_credentials' or 'both'."
                )

        if 'require_demographic_scopes' in self.cleaned_data and 'scope' in self.cleaned_data:
            require_demographic_scopes = self.cleaned_data['require_demographic_scopes']
            scope = self.cleaned_data['scope']

            demographic_scopes_query = scope.filter(slug__in=BENE_PERSONAL_INFO_SCOPES)
            if require_demographic_scopes:
                if not demographic_scopes_query.exists():
                    raise ValidationError(
                        'Must have at least one demographic scope when require_demographic_scopes==True.'
                    )
            else:  # False or None
                if demographic_scopes_query.exists():
                    raise ValidationError(
                        'Cannot have demographic scopes when require_demographic_scopes==False or None.'
                    )

        return self.cleaned_data

    @override
    def clean_agree(self):
        return self.cleaned_data.get('agree')

    @override
    def save(self, *args, **kwargs):
        user_mode = self.cleaned_data.get('user_mode')
        client_secret_action = self.cleaned_data.get('client_secret_action')
        app = self.instance
        # If the application is new (i.e., it doesn't have a primary key yet), we set some default values for the application fields.
        if app.pk is None:
            app.agree = True
            app.authorization_grant_type = Application.GRANT_AUTHORIZATION_CODE
            app.client_type = Application.CLIENT_CONFIDENTIAL
        if user_mode == 'new':
            # If the user_mode is 'new', we create a new user and associate it with the application
            # This returns a tuple of (user, created), where 'created' is a boolean indicating if the
            # user was created or already existed.  We don't use the 'created' value here, but it could
            # be useful for logging or other purposes.
            new_user_model, created = User.objects.get_or_create(
                username=self.cleaned_data.get('name') + '@example.com',
                password=str(uuid.uuid4()),
                is_active=True,
            )
            group = Group.objects.get(name='BlueButton')
            new_user_model.groups.add(group)
            new_user_model.save()

            UserProfile.objects.get_or_create(
                user=new_user_model,
                organization_name=self.cleaned_data.get('organization_name'),
            )
            app.user = new_user_model

        if client_secret_action == NO_CLIENT_SECRET:
            app.hash_client_secret = False
            app.client_secret = ''
            app.client_secret_plain = ''
        elif client_secret_action == GENERATE_CLIENT_SECRET:
            app.hash_client_secret = True
            app.client_secret_plain = generate_client_secret()
            app.client_secret = app.client_secret_plain
        elif client_secret_action == NO_CHANGE:
            pass

        # Use Models.form save here and not CustomRegisterApplicationForm's save method here,
        # because we don't want the scopes override or agree logging parts of CustomRegisterApplicationForm's
        # save method to run here
        app = super(CustomRegisterApplicationForm, self).save(*args, **kwargs)
        uri = app.store_media_file(self.cleaned_data.pop('logo_image', None))
        if uri:
            app.logo_uri = uri
            app.save()
        return app


class EditApplicationForm(CreateApplicationForm):
    CLIENT_SECRET_ACTION_CHOICES = [
        (GENERATE_CLIENT_SECRET, 'Generate a new client secret'),
        (NO_CLIENT_SECRET, 'Remove the existing client secret'),
        # Add a choice to leave the existing client secret unchanged,
        # which is the default behavior when editing an application
        (NO_CHANGE, 'Leave the existing client secret unchanged'),
    ]
    client_secret_action = forms.ChoiceField(choices=CLIENT_SECRET_ACTION_CHOICES, initial=NO_CHANGE, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We don't need the ability to choose the user mode for editing an application,
        # so we hide it from the form and set it to an 'existing' user mode.
        if 'user_mode' in self.fields:
            self.fields['user_mode'].initial = 'existing'
            self.fields['user_mode'].widget = forms.HiddenInput()
            self.fields['user_mode'].required = False
        self.fields['user'].label = 'User*'
        self.fields['user'].required = True
        self.fields['authorization_grant_type'].choices = settings.GRANT_TYPES
        self.fields['authorization_grant_type'].label = 'Authorization Grant Type*'
        self.fields['redirect_uris'].label = 'Redirect URIs*'
        # Hide the organization_name field since it's not part of the Application model
        # and is only used for creating new users
        self.fields['organization_name'].required = False
        self.fields['organization_name'].widget = forms.HiddenInput()
        self.fields['scope'].label = 'Scopes*'
        self.fields['client_type'].label = 'Client Type*'
        self.fields['client_id'].label = 'Client ID*'
        self.fields['data_access_type'].label = 'Data Access Type*'

    class Meta:
        model = get_application_model()
        fields = (
            'data_access_type',
            'client_secret_action',
            'client_id',
            'user',
            'client_type',
            'user_mode',
            'authorization_grant_type',
            'client_secret_plain',
            'client_secret',
            'name',
            'skip_authorization',
            'scope',
            'require_demographic_scopes',
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
            'internal_application_labels',
            'active',
            'first_active',
            'last_active',
            'jwks_uri',
            'allowed_auth_type',
            'part_d_eob_only',
        )


class SimpleAllowForm(DotAllowForm):
    code_challenge = forms.CharField(required=False, widget=forms.HiddenInput())
    code_challenge_method = forms.CharField(required=False, widget=forms.HiddenInput())
    share_demographic_scopes = forms.CharField(required=False)
    share_samhsa_data = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        scope = cleaned_data.get('scope', None)

        if scope is None:
            cleaned_data['scope'] = ''
            scope = ''
        else:
            cleaned_scope_list = CapabilitiesScopes().condense_scopes(scope.split(' '))
            # Remove demographic information scopes, if beneficiary is not sharing
            if cleaned_data.get('share_demographic_scopes') != 'True':
                cleaned_scope_list = CapabilitiesScopes().remove_demographic_scopes(cleaned_scope_list)
            cleaned_data['scope'] = ' '.join(cleaned_scope_list)

        return cleaned_data
