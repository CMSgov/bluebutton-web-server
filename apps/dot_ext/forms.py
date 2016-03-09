from __future__ import absolute_import
from __future__ import unicode_literals

from django.forms import ModelForm
from oauth2_provider.models import get_application_model
from ..capabilities.models import ProtectedCapability


class CustomRegisterApplicationForm(ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(CustomRegisterApplicationForm, self).__init__(*args, **kwargs)
        choices = []
        groups = user.groups.values_list('id', flat=True)
        for g in groups:
            pcs = ProtectedCapability.objects.filter(group=g)
            for i in pcs:
                choices.append([i.pk, i.title])
        self.fields['scope'].choices = choices

    class Meta:
        model = get_application_model()
        fields = ('scope', 'name', 'client_id', 'client_secret', 'client_type',
                  'authorization_grant_type', 'redirect_uris')

    required_css_class = 'required'
