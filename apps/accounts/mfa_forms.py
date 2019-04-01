from django import forms
from django.utils.translation import ugettext_lazy as _


class MFACodeForm(forms.Form):
    code = forms.CharField(widget=forms.PasswordInput, max_length=30,
                           label=_('Code*'))
    required_css_class = 'required'
