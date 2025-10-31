from django.urls import re_path
from django.contrib import admin

from apps.fhir.bluebutton.views.read import (
    ReadViewCoverage,
    ReadViewExplanationOfBenefit,
    ReadViewPatient,
)
from apps.fhir.bluebutton.views.search import (
    SearchViewCoverage,
    SearchViewExplanationOfBenefit,
    SearchViewPatient,
)

from apps.fhir.bluebutton.views import smart_configuration 

admin.autodiscover()

urlpatterns = [
    # OpenID Connect (OIDC)
    url(r'.well-known/smart-configuration$',
        smart_configuration,
        name='smart-configuration-v2'),

    # Patient ReadView
    re_path(
        r"Patient/(?P<resource_id>[^/]+)",
        ReadViewPatient.as_view(version=2),
        name="bb_oauth_fhir_patient_read_or_update_or_delete_v2",
    ),
    # Patient SearchView
    re_path(
        r"Patient[/]?",
        SearchViewPatient.as_view(version=2),
        name="bb_oauth_fhir_patient_search_v2",
    ),
    # Coverage ReadView
    re_path(
        r"Coverage/(?P<resource_id>[^/]+)",
        ReadViewCoverage.as_view(version=2),
        name="bb_oauth_fhir_coverage_read_or_update_or_delete_v2",
    ),
    # Coverage SearchView
    re_path(
        r"Coverage[/]?",
        SearchViewCoverage.as_view(version=2),
        name="bb_oauth_fhir_coverage_search_v2",
    ),
    # EOB ReadView
    re_path(
        r"ExplanationOfBenefit/(?P<resource_id>[^/]+)",
        ReadViewExplanationOfBenefit.as_view(version=2),
        name="bb_oauth_fhir_eob_read_or_update_or_delete_v2",
    ),
    # EOB SearchView
    re_path(
        r"ExplanationOfBenefit[/]?",
        SearchViewExplanationOfBenefit.as_view(version=2),
        name="bb_oauth_fhir_eob_search_v2",
    ),
]
