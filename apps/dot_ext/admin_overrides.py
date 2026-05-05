# Putting this in a separate file to avoid circular imports

from django import forms
from django.core.exceptions import ValidationError
from oauth2_provider.admin import ApplicationAdmin
from oauth2_provider.models import get_application_model

from apps.dot_ext.constants import BENE_PERSONAL_INFO_SCOPES


class AnotherApplicationAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()

        if 'require_demographic_scopes' in cleaned_data and 'scope' in cleaned_data:
            require_demographic_scopes = cleaned_data['require_demographic_scopes']
            scope = cleaned_data['scope']

            demographic_scopes_query = scope.filter(slug__in=BENE_PERSONAL_INFO_SCOPES)
            if require_demographic_scopes is False:
                if demographic_scopes_query.exists():
                    raise ValidationError('Cannot have demographic scopes when require_demographic_scopes==False.')
            else:  # True or None
                if not demographic_scopes_query.exists():
                    raise ValidationError(
                        'Must have at least one demographic scope when require_demographic_scopes==True or None.'
                    )

        return cleaned_data

    class Meta:
        model = get_application_model()
        fields = '__all__' # TODO this is strongly recommended against


class AnotherApplicationAdmin(ApplicationAdmin):
    form = AnotherApplicationAdminForm
