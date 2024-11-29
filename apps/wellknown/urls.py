from django.urls import path
from waffle.decorators import waffle_switch
from .views import (
    openid_configuration,
    smart_configuration,
    ApplicationListView,
    ApplicationLabelView,
    PublicApplicationListView,
)


urlpatterns = [
    path("openid-configuration", openid_configuration, name="openid-configuration"),
    path("smart-configuration", smart_configuration, name="smart-configuration"),
    path(
        "applications",
        waffle_switch("wellknown_applications")(ApplicationListView.as_view()),
        name="applications-list",
    ),
    path(
        "application-labels",
        waffle_switch("wellknown_applications")(ApplicationLabelView.as_view()),
        name="application-labels",
    ),
    path(
        "public-applications",
        waffle_switch("wellknown_applications")(PublicApplicationListView.as_view()),
        name="public-applications-list",
    ),
    path(
        "openid-configuration-v2", openid_configuration, name="openid-configuration-v2"
    ),
    path(
        "smart-configuration-v2", smart_configuration, name="smart-on-fhir-configuration-v2"
    ),
    path(
        "applications-v2",
        waffle_switch("wellknown_applications")(ApplicationListView.as_view()),
        name="applications-list-v2",
    ),
    path(
        "application-labels-v2",
        waffle_switch("wellknown_applications")(ApplicationLabelView.as_view()),
        name="application-labels-v2",
    ),
    path(
        "public-applications-v2",
        waffle_switch("wellknown_applications")(PublicApplicationListView.as_view()),
        name="public-applications-list-v2",
    ),
]
