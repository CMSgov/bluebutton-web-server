"""
This module is largely inspired by django-rest-framework and django oauth toolkit settings.

Settings for connecting to the FHIR server are all namespaced in the FHIR_SERVER setting.
For example your project's `settings.py` file might look like this:

FHIR_SERVER = {
    "URL": "https://fhir.server/baseDstu3/",
}

"""
from django.conf import settings


USER_SETTINGS = getattr(settings, "FHIR_SERVER", None)

DEFAULTS = {
    "FHIR_URL": None,
    "CLIENT_AUTH": False,
    "CERT_FILE": "",
    "KEY_FILE": "",
    "SERVER_VERIFY": False,
    "WAIT_TIME": 30,
    "VERIFY_SERVER": False,
}

# List of settings that cannot be empty
MANDATORY = (
    "FHIR_URL",
)


class FHIRServerSettings(object):

    def __init__(self, user_settings=None, defaults=None, mandatory=None):
        self.user_settings = user_settings or {}
        self.defaults = defaults or {}
        self.mandatory = mandatory or ()

    def __getattr__(self, attr):
        attr = attr.upper()
        if attr not in self.defaults.keys():
            raise AttributeError("Invalid FHIRServer setting: %r" % (attr))

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        self.validate_setting(attr, val)

        # Cache the result
        setattr(self, attr, val)
        return val

    def validate_setting(self, attr, val):
        if not val and attr in self.mandatory:
            raise AttributeError("FHIRServer setting: %r is mandatory" % (attr))


fhir_settings = FHIRServerSettings(USER_SETTINGS, DEFAULTS, MANDATORY)
