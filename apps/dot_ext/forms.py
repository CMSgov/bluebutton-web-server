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
        self.fields['authorization_grant_type'].choices = settings.GRANT_TYPES
        self.fields['client_type'].initial = 'confidential'
        self.fields['agree'].label = mark_safe(agree_label)
        self.fields['name'].label = "Name*"
        self.fields['name'].required = True
        self.fields['client_type'].label = "Client Type*"
        self.fields['authorization_grant_type'].label = "Authorization Grant Type*"
        self.fields['redirect_uris'].label = "Redirect URIs*"

    class Meta:
        model = get_application_model()
        fields = ('name', 'scope', 'client_type',
                  'authorization_grant_type', 'redirect_uris',
                  'logo_uri', 'policy_uri', 'tos_uri', 'contacts',
                  'agree')

    required_css_class = 'required'

    def clean_agree(self):
        agree = self.cleaned_data.get('agree')
        if not agree:
            msg = _('You must agree to the API Terms of Service Agreement"')
            raise forms.ValidationError(msg)
        return agree

    def clean_redirect_uris(self):
        redirect_uris = self.cleaned_data.get('redirect_uris')
        if getattr(settings, 'REQUIRE_HTTPS_REDIRECT_URIS', False):
            if redirect_uris:
                for u in redirect_uris.split():
                    if not u.startswith("https://"):
                        msg = _('Redirect URIs are required to use https.')
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
