from django.urls import re_path
from django.contrib import admin
from waffle.decorators import waffle_switch

from apps.fhir.bluebutton.views.read import (
    ReadViewCoverage,
    ReadViewExplanationOfBenefit,
)
from apps.fhir.bluebutton.views.search import (
    SearchViewCoverage,
    SearchViewExplanationOfBenefit,
)
from apps.fhir.bluebutton.views.patient_viewset import PatientViewSet
from apps.fhir.bluebutton.views.insurancecard_viewset import DigitalInsuranceCardViewSet

admin.autodiscover()

urlpatterns = [
    # Patient ReadView
    re_path(
        r'Patient/(?P<resource_id>[^/]+)',
        waffle_switch('v3_endpoints')(PatientViewSet.as_view({'get': 'retrieve'}, version=3)),
        name='bb_oauth_fhir_patient_read_or_update_or_delete_v3',
    ),
    # Patient SearchView
    re_path(
        r'Patient[/]?',
        waffle_switch('v3_endpoints')(PatientViewSet.as_view({'get': 'list'}, version=3)),
        name='bb_oauth_fhir_patient_search_v3',
    ),
    # Coverage ReadView
    re_path(
        r'Coverage/(?P<resource_id>[^/]+)',
        waffle_switch('v3_endpoints')(ReadViewCoverage.as_view(version=3)),
        name='bb_oauth_fhir_coverage_read_or_update_or_delete_v3',
    ),
    # Coverage SearchView
    re_path(
        r'Coverage[/]?',
        waffle_switch('v3_endpoints')(SearchViewCoverage.as_view(version=3)),
        name='bb_oauth_fhir_coverage_search_v3',
    ),
    # EOB ReadView
    re_path(
        r'ExplanationOfBenefit/(?P<resource_id>[^/]+)',
        waffle_switch('v3_endpoints')(ReadViewExplanationOfBenefit.as_view(version=3)),
        name='bb_oauth_fhir_eob_read_or_update_or_delete_v3',
    ),
    # EOB SearchView
    re_path(
        r'ExplanationOfBenefit[/]?',
        waffle_switch('v3_endpoints')(SearchViewExplanationOfBenefit.as_view(version=3)),
        name='bb_oauth_fhir_eob_search_v3',
    ),
    # C4DIC
    # Digital Insurance Card ViewSet
    # TODO - Change the URI for this endpoint when we finalize
    # TODO - We are sending this to list even though it is a retrieve BECAUSE we're not asking for a resource id by the
    # application, which means we're kinda breaking REST principles here.
    re_path(
        r'DigitalInsuranceCard[/]?',
        waffle_switch('v3_endpoints')(DigitalInsuranceCardViewSet.as_view({'get': 'list'}, version=3)),
        name='bb_oauth_fhir_dic_read',
    ),
]
