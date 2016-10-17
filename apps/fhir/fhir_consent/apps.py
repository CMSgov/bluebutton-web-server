from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

# Setting is required in __init__.py
# default_app_config = 'apps.fhir.fhir_consent.apps.fhir_consentConfig'


class fhir_consentConfig(AppConfig):
    name = 'apps.fhir.fhir_consent'
    verbose_name = _("fhir_consent")

    def ready(self):
        import apps.fhir.fhir_consent.signals  # NOQA
        # import fhir_consent.signals
