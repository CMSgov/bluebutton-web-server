# Putting this in a separate file to avoid circular imports

from django import forms
from django.core.exceptions import ValidationError
from oauth2_provider.admin import ApplicationAdmin
from oauth2_provider.models import get_application_model

from apps.dot_ext.constants import BENE_PERSONAL_INFO_SCOPES


class ValidatedApplicationAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()

        if 'require_demographic_scopes' in cleaned_data and 'scope' in cleaned_data:
            require_demographic_scopes = cleaned_data['require_demographic_scopes']
            scope = cleaned_data['scope']

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

        return cleaned_data

    class Meta:
        model = get_application_model()
        fields = [
            'data_access_type',
            'client_id',
            'user',
            'client_type',
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
            'allowed_auth_type',
            'jwks_uri',
        ]


class ValidatedApplicationAdmin(ApplicationAdmin):
    form = ValidatedApplicationAdminForm
