from django import forms
from django.core.validators import RegexValidator

# from phonenumber_field.formfields import PhoneNumberField

SHARING_FREQUENCY_CHOICES = [
    ("one_time", "One-Time Collection"),
    ("bene_action", "Only when beneficiaries take a specific action"),
    ("daily", "Data is shared with third-parties daily"),
    ("weekly", "Data is shared with third-parties weekly"),
    ("monthly", "Data is shared with third-parties monthly"),
    ("other", "Other"),
    ("not_shared", "Not shared"),
]

WITHDRAWN_CONSENT_CHOICES = [
    ("delete", "We securely delete the user data"),
    ("delete_on_request", "We keep the data, but will delete on user request"),
    ("keep", "We keep the data, and will not delete it"),
    ("other", "Other"),
]


class InterimProdAccessForm(forms.Form):
    application_name = forms.CharField()
    application_description = forms.CharField()
    application_url = forms.URLField()
    terms_of_service_url = forms.URLField()
    privacy_policy_url = forms.URLField()
    us_based = forms.BooleanField()
    point_of_contact_email = forms.EmailField()
    point_of_contact_phone_number = forms.CharField(
        max_length=17,
        validators=[
            RegexValidator(
                r"^\+?1?\d{9,15}$",
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
            )
        ],
    )
    adheres_to_bb2_tos = forms.BooleanField()
    user_discovery_path = forms.Textarea()
    easy_to_read_pp = forms.BooleanField()
    does_pp_follow_bb2_guidelines = forms.BooleanField()
    doesnt_follow_pp_guidelines_reason = forms.Textarea()
    third_party_app_data_sharing_frequency = forms.ChoiceField(
        choices=SHARING_FREQUENCY_CHOICES
    )
    action_for_withdrawn_consent = forms.ChoiceField(choices=WITHDRAWN_CONSENT_CHOICES)
    data_sharing_consent_method = forms.Textarea()
    vendor_data_protection = forms.Textarea()
    data_use_post_sale = forms.Textarea()
    partner_requirements_consent = forms.BooleanField()
    data_storage_technique = forms.Textarea()
    organization_authority_assertion = forms.BooleanField()
