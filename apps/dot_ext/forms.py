from django.utils.safestring import mark_safe
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from oauth2_provider.forms import AllowForm as DotAllowForm
from oauth2_provider.models import get_application_model
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.validators import urlsplit
from django.core.validators import URLValidator
import logging


logger = logging.getLogger('hhs_server.%s' % __name__)



class CustomRegisterApplicationForm(forms.ModelForm):

    def __init__(self, user, *args, **kwargs):
        agree_label = u'Yes I have read and agree to the <a target="_blank" href="%s">API Terms of Service Agreement</a>*' % (
            settings.TOS_URI)
        super(CustomRegisterApplicationForm, self).__init__(*args, **kwargs)
        self.fields['authorization_grant_type'].choices = settings.GRANT_TYPES
        self.fields['client_type'].initial = 'confidential'
        self.fields['agree'].label = mark_safe(agree_label)
        self.fields['name'].label = "Name*"
        self.fields['name'].required = True
        self.fields['client_type'].label = "Client Type*"
        self.fields[
            'authorization_grant_type'].label = "Authorization Grant Type*"
        self.fields['redirect_uris'].label = "Redirect URIs*"

    class Meta:
        model = get_application_model()
        fields = ('name',
                  'client_type',
                  'authorization_grant_type', 'redirect_uris',
                  'logo_uri', 'client_uri', 'policy_uri', 'tos_uri', 'contacts',
                  'agree')

    required_css_class = 'required'

    def clean(self):
        client_type = self.cleaned_data.get('client_type')
        authorization_grant_type = self.cleaned_data.get(
            'authorization_grant_type')
        redirect_uris = self.cleaned_data.get('redirect_uris')

        msg = ""
        validate_error = False
        # Public clients don't use authorization-code flow
        if client_type == 'public' and authorization_grant_type == 'authorization-code':
            validate_error = True
            msg += 'A public client may not request ' \
                   'an authorization-code grant type.'

        # Confidential clients cannot use implicit authorization_grant_type
        if client_type == 'confidential' and authorization_grant_type == 'implicit':
            validate_error = True
            msg += 'A confidential client may not ' \
                   'request an implicit grant type.'

        # Confidential clients cannot use implicit authorization_grant_type
        if client_type == 'confidential' and authorization_grant_type == 'implicit':
            validate_error = True
            msg += 'A confidential client may not ' \
                   'request an implicit grant type.'

        # Native mobile applications using RCF 8252 must supply https or
        # LL00000000
        for uri in redirect_uris.split():
            scheme, netloc, path, query, fragment = urlsplit(uri)

            valid_schemes = get_allowed_schemes()

            if scheme in valid_schemes:
                validate_error = False
            else:
                validate_error = True

            if validate_error:
                msg += '%s is an invalid scheme. Redirect URIs must use %s ' \
                    % (scheme, ' or '.join(valid_schemes))

        if validate_error:
            msg_output = _(msg)
            raise forms.ValidationError(msg_output)
        else:
            pass

        return self.cleaned_data

    def clean_name(self):
        name = self.cleaned_data.get('name')
        app_model = get_application_model()
        if app_model.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("""
                                        It looks like this application name
                                        is already in use with another app.
                                        Please enter a different application
                                        name to prevent future errors.
                                        Note that names are case-insensitive.
                                        """)
        return name

    def clean_client_type(self):
        client_type = self.cleaned_data.get('client_type')
        authorization_grant_type = self.cleaned_data.get(
            'authorization_grant_type')
        if client_type == 'public' and authorization_grant_type == 'authorization-code':
            msg = _(
                'A public client may not request an '
                'authorization-code grant type.')
            raise forms.ValidationError(msg)
        return client_type

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
                    if u.startswith("http://"):
                        msg = _('Redirect URIs must not use http.')
                        raise forms.ValidationError(msg)
        return redirect_uris

    def clean_client_uri(self):
        client_uri = self.cleaned_data.get('client_uri')
        if client_uri:
            validator = URLValidator()
            try:
                validator(client_uri)
            except:
                raise forms.ValidationError('Please enter a valid URI. For example, "https://www.example.org"')
        return client_uri

    def save(self, *args, **kwargs):
        app = self.instance
        logmsg = "%s agreed to %s for the application %s" % (app.user, app.op_tos_uri,
                                                             app.name)
        logger.info(logmsg)
        return super().save(*args, **kwargs)


class SimpleAllowForm(DotAllowForm):
    code_challenge = forms.CharField(required=False, widget=forms.HiddenInput())
    code_challenge_method = forms.CharField(required=False, widget=forms.HiddenInput())

    # def is_valid(self):
    #     raise Exception(self)


def get_allowed_schemes():
    """
    get allowed_schemes set in OAUTH2_PROVIDER.ALLOWED_REDIRECT_URI_SCHEMES
    :return: list
    """
    if oauth2_settings.ALLOWED_REDIRECT_URI_SCHEMES:
        valid_list = oauth2_settings.ALLOWED_REDIRECT_URI_SCHEMES
    else:
        valid_list = ['https', ]

    return valid_list
