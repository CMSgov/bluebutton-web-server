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

APPLICATION_CATEGORIES = [
    ("research", "Research"),
    ("plan_finders", "Plan Finders"),
    ("agent_brokers", "Agent Brokers"),
    ("symptom_checker", "Symptom Checker"),
    ("organize_share_medical_claims", "Organize & Share Medical Claims"),
    ("other", "Other"),
]


class InterimProdAccessForm(forms.Form):

    # card_name = forms.CharField(max_length=100, label="Cardholder Name")
    # card_number = forms.CharField(max_length=50, label="Card Number")
    # card_code = forms.CharField(max_length=20, label="Security Code")
    # card_expirate_time = forms.CharField(max_length=100, label="Expiration (MM/YYYY)")

    # Fields needed compared to https://airtable.com/app4N2CBNxgseqVyq/tbl61MNkxjOG19Aiz/viw1R5g2rbE7S2YFr?blocks=hide
    # Application Category

    application_name = forms.CharField()
    application_description = forms.CharField()
    application_url = forms.URLField()
    terms_of_service_url = forms.URLField()
    privacy_policy_url = forms.URLField()
    us_based = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "ds-c-choice"})
    )
    associated_sandbox_users = forms.CharField(widget=forms.Textarea())
    application_category = forms.ChoiceField(choices=APPLICATION_CATEGORIES)
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
    adheres_to_bb2_tos = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "ds-c-choice"})
    )
    user_discovery_path = forms.CharField(widget=forms.Textarea())
    easy_to_read_pp = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "ds-c-choice"})
    )
    does_pp_follow_bb2_guidelines = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "ds-c-choice"})
    )
    doesnt_follow_pp_guidelines_reason = forms.CharField(widget=forms.Textarea())
    third_party_app_data_sharing_frequency = forms.ChoiceField(
        choices=SHARING_FREQUENCY_CHOICES
    )
    action_for_withdrawn_consent = forms.ChoiceField(choices=WITHDRAWN_CONSENT_CHOICES)
    data_sharing_consent_method = forms.CharField(widget=forms.Textarea())
    vendor_data_protection = forms.CharField(widget=forms.Textarea())
    data_use_post_sale = forms.CharField(widget=forms.Textarea())
    partner_requirements_consent = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "ds-c-choice"})
    )
    data_storage_technique = forms.CharField(widget=forms.Textarea())
    organization_authority_assertion = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "ds-c-choice"})
    )
