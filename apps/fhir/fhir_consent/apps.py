from __future__ import absolute_import
from __future__ import unicode_literals
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class fhir_consentConfig(AppConfig):
    # name = 'apps.fhir.fhir_consent'
    name = 'apps.fhir.fhir_consent'
    verbose_name = _("FHIR Consent")
