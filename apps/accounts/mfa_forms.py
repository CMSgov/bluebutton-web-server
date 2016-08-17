from django import forms

from django.utils.translation import ugettext_lazy as _


class MFACodeForm(forms.Form):
    code = forms.CharField(widget=forms.PasswordInput, max_length=30,
                           label=_('Code*'))
    required_css_class = 'required'


class LoginForm(forms.Form):
    username = forms.CharField(max_length=30, label=_('User'))
    password = forms.CharField(widget=forms.PasswordInput, max_length=30,
                               label=_('Password'))
    required_css_class = 'required'
