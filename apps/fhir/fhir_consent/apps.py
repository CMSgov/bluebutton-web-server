from django.apps import AppConfig


class fhir_consent_config(AppConfig):
    name = 'fhir_consent'
    verbose_name = "fhir consent recorder"

    def ready(self):
        import fhir_consent.signals  # NOQA
