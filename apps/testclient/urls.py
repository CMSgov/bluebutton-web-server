from django.urls import path

from .views import (
    # all versions
    callback,
    restart,
    test_links,

    # v1
    authorize_link_v1,
    test_coverage_v1,
    test_eob_v1,
    test_metadata_v1,
    test_openid_config_v1,
    test_patient_v1,
    test_userinfo_v1,

    # v2
    authorize_link_v2,
    test_coverage_v2,
    test_eob_v2,
    test_metadata_v2,
    test_openid_config_v2,
    test_patient_v2,
    test_userinfo_v2,

    # v3
    authorize_link_v3,
    test_coverage_v3,
    test_eob_v3,
    test_metadata_v3,
    test_openid_config_v3,
    test_patient_v3,
    test_userinfo_v3,

    # c4dic
    test_digital_insurance_card_v3

)

urlpatterns_unversioned = [
    path('callback', callback, name='testclient-callback'),
    path('restart', restart, name='testclient-restart'),
    path('', test_links, name='test_links'),
]

urlpatterns_v1 = [
    path('authorize-link', authorize_link_v1, name='authorize_link'),
    path('Coverage', test_coverage_v1, name='test_coverage'),
    path('ExplanationOfBenefit', test_eob_v1, name='test_eob'),
    path('metadata', test_metadata_v1, name='test_metadata'),
    path('openidConfig', test_openid_config_v1, name='test_openid_config'),
    path('Patient', test_patient_v1, name='test_patient'),
    path('userinfo', test_userinfo_v1, name='test_userinfo'),
]

urlpatterns_v2 = [
    path('authorize-link-v2', authorize_link_v2, name='authorize_link_v2'),
    path('CoverageV2', test_coverage_v2, name='test_coverage_v2'),
    path('ExplanationOfBenefitV2', test_eob_v2, name='test_eob_v2'),
    path('metadataV2', test_metadata_v2, name='test_metadata_v2'),
    path('openidConfigV2', test_openid_config_v2, name='test_openid_config_v2'),
    path('PatientV2', test_patient_v2, name='test_patient_v2'),
    path('userinfoV2', test_userinfo_v2, name='test_userinfo_v2'),
]

urlpatterns_v3 = [
    path('authorize-link-v3', authorize_link_v3, name='authorize_link_v3'),
    path('CoverageV3', test_coverage_v3, name='test_coverage_v3'),
    path('ExplanationOfBenefitV3', test_eob_v3, name='test_eob_v3'),
    path('metadataV3', test_metadata_v3, name='test_metadata_v3'),
    path('openidConfigV3', test_openid_config_v3, name='test_openid_config_v3'),
    path('PatientV3', test_patient_v3, name='test_patient_v3'),
    path('userinfoV3', test_userinfo_v3, name='test_userinfo_v3'),
    path('DigitalInsuranceCard', test_digital_insurance_card_v3, name='test_digital_insurance_card_v3'),
]

urlpatterns = urlpatterns_unversioned + urlpatterns_v1 + urlpatterns_v2 + urlpatterns_v3
