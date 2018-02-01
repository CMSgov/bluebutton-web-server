from __future__ import absolute_import
from __future__ import unicode_literals

from django.utils.safestring import mark_safe
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from oauth2_provider.forms import AllowForm as DotAllowForm
from oauth2_provider.models import get_application_model
from oauth2_provider.scopes import get_scopes_backend
from apps.capabilities.models import ProtectedCapability
from .oauth2_validators import set_regex, compare_to_regex

__author__ = "Alan Viars"


class CustomRegisterApplicationForm(forms.ModelForm):

    def __init__(self, user, *args, **kwargs):
        agree_label = u'Yes I have read and agree to the <a target="_blank" href="%s">API Terms of Service Agreement</a>*' % (
            settings.TOS_URI)
        super(CustomRegisterApplicationForm, self).__init__(*args, **kwargs)
        choices = []
        groups = user.groups.values_list('id', flat=True)
        for g in groups:
            pcs = ProtectedCapability.objects.filter(group=g)
            for i in pcs:
                choices.append([i.pk, i.title])
        self.fields['scope'].choices = choices
        self.fields['scope'].label = "Scope*"
        self.fields['scope'].initial = pcs
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
        fields = ('name', 'scope', 'client_type',
                  'authorization_grant_type', 'redirect_uris',
                  'logo_uri', 'policy_uri', 'tos_uri', 'contacts',
                  'agree')

    required_css_class = 'required'

    def clean(self):
        client_type = self.cleaned_data.get('client_type')
        authorization_grant_type = self.cleaned_data.get(
            'authorization_grant_type')
        redirect_uris = self.cleaned_data.get('redirect_uris')

        # Public clients dont use authorization-cod flow
        if client_type == 'public' and authorization_grant_type == 'authorization-code':
            msg = _(
                'A public client may not request an authorization-code grant type.')
            raise forms.ValidationError(msg)

        # Confidential clients cannot use implicit authorization_grant_type
        if client_type == 'confidential' and authorization_grant_type == 'implicit':
            msg = _('A confidential client may not request an implicit grant type.')
            raise forms.ValidationError(msg)

        # Confidential clients cannot use implicit authorization_grant_type
        if client_type == 'confidential' and authorization_grant_type == 'implicit':
            msg = _('A confidential client may not request an implicit grant type.')
            raise forms.ValidationError(msg)

        # Native mobile applications using RCF 8252 must supply https or
        # LL00000000
        for uri in redirect_uris.split():
            regex = set_regex()
            if compare_to_regex(regex, uri) or not uri.startswith("https://"):
                msg = _(
                    'Redirect URIs for native mobile applications must use https:// or ??00000000:://.')
                raise forms.ValidationError(msg)
        return self.cleaned_data

    def clean_client_type(self):
        client_type = self.cleaned_data.get('client_type')
        authorization_grant_type = self.cleaned_data.get(
            'authorization_grant_type')

        print(client_type, authorization_grant_type)
        if client_type == 'public' and authorization_grant_type == 'authorization-code':
            msg = _(
                'A public client may not request an authorization-code grant type.')
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


class SimpleAllowForm(DotAllowForm):
    pass


class AllowForm(DotAllowForm):
    scope = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)
    expires_in = forms.TypedChoiceField(choices=settings.DOT_EXPIRES_IN, coerce=int,
                                        empty_value=None,
                                        label="Access to this application expires in")

    def __init__(self, *args, **kwargs):
        application = kwargs.pop('application', None)

        if application is None:
            super(AllowForm, self).__init__(*args, **kwargs)
        else:
            # we use the application instance to get the list of available scopes
            # because it is needed to create the choices list for the `scope`
            # field.
            available_scopes = get_scopes_backend().get_available_scopes(application)

            # set the available_scopes as the initial value so that
            # all checkboxes are checked
            kwargs['initial']['scope'] = available_scopes

            # init the form to create self.fields
            super(AllowForm, self).__init__(*args, **kwargs)

            # get the list of all the scopes available in the system
            # to get the description of each available scope.
            all_scopes = get_scopes_backend().get_all_scopes()
            choices = [(scope, all_scopes[scope])
                       for scope in available_scopes]
            self.fields['scope'].choices = choices
