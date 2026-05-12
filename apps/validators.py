from django.core.validators import RegexValidator


# FROM https://stackoverflow.com/questions/19130942/whats-the-best-way-to-store-phone-number-in-django-models
# removed the `1?` because E.164 phone numbers can be up to 15 digits long,
# which *includes* the country code
phone_regex = RegexValidator(
    regex=r'^\+?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
)
