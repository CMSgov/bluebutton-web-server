from django.urls import path
from waffle.decorators import waffle_switch
from .views import (
    openid_configuration_v1,
    openid_configuration_v2,
    openid_configuration_v3,
    ApplicationListView,
    ApplicationLabelView,
    PublicApplicationListView,
)


urlpatterns = [
    # NOTE: the openid-configuration paths are essentially legacy paths. We continue to carry them to
    # make sure we do not break downstream applications. However, the `hhs_oath_server` code *also* has
    # paths for openid-configuration. Those have the shape
    #
    # "{version}/connect/.well-known/openid-configuration"
    #
    # which differs from the versioned paths here. They all call the same functions/views
    # as a result (openid_configuration_v1, openid_configuration_v2, etc.).
    path("openid-configuration", openid_configuration_v1, name="openid-configuration"),
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
        "openid-configuration-v2", openid_configuration_v2, name="openid-configuration-v2"
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
    path(
        "openid-configuration-v3", waffle_switch("v3_endpoints")(openid_configuration_v3), name="openid-configuration-v3"
    ),
]
