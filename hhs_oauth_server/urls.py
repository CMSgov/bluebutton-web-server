from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from django.urls import include, path, re_path
from django.contrib import admin
from waffle.decorators import waffle_switch
from waffle import switch_is_active

from apps.accounts.views.oauth2_profile import openidconnect_userinfo_v1, openidconnect_userinfo_v2, openidconnect_userinfo_v3
from apps.fhir.bluebutton.views.home import fhir_conformance_v1, fhir_conformance_v2, fhir_conformance_v3
from apps.wellknown.views.openid import smart_configuration_v1, smart_configuration_v2, smart_configuration_v3
from apps.wellknown.views.openid import openid_configuration_v1, openid_configuration_v2, openid_configuration_v3

from hhs_oauth_server.hhs_oauth_server_context import IsAppInstalled
from .views import testobject

admin.autodiscover()
admin.site.enable_nav_sidebar = False

ADMIN_REDIRECTOR = getattr(settings, "ADMIN_PREPEND_URL", "")

##################
# NOTE: The waffle_switch('...')(...) construct can ONLY be used for
# views and functions. It is a decorator. It cannot wrap an `include(...)` statement.
##################


def robots_txt(request):
    return HttpResponse(
        "User-agent: *\nDisallow: /v1/o/\nDisallow: /v2/o/\nDisallow: /v3/o/",
        content_type="text/plain",
    )


all_versions = [
    path("health/", include("apps.health.urls")),
    path("docs/", include("apps.docs.urls")),
    re_path(r"^" + ADMIN_REDIRECTOR + "admin/metrics/", include("apps.metrics.urls")),
    re_path(r"^" + ADMIN_REDIRECTOR + "admin/", admin.site.urls),
    path("creds", include("apps.creds.urls")),
    path("akamai/testobject", testobject, name="akamai_testobject"),
    path("robots.txt", robots_txt),
    re_path(r"^.well-known/", include("apps.wellknown.urls")),
]

# NOTE: the openid-configuration paths are defined slightly differently here and in
# `wellknown`, in order not to break existing/legacy applications.
# They all call the same functions/views
# as a result (openid_configuration_v1, openid_configuration_v2, etc.).

urlpatterns_v1 = [
    # accounts
    path("v1/accounts/", include("apps.accounts.urls")),
    # authorization
    path("v1/o/", include("apps.authorization.urls")),
    # connect/userinfo
    re_path(
        r"^v1/connect/userinfo", openidconnect_userinfo_v1, name="openid_connect_userinfo"
    ),
    # dot_ext
    path("v1/o/", include("apps.dot_ext.urls")),
    # fhir/bluebutton
    path("v1/fhir/", include("apps.fhir.bluebutton.urls")),
    # fhir/metadata
    path("v1/fhir/metadata", fhir_conformance_v1, name="fhir_conformance_metadata"),
    # openid_config
    path(
        "v1/connect/.well-known/openid-configuration", openid_configuration_v1, name="openid-configuration"
    ),
    # smart config
    path("v1/fhir/.well-known/smart-configuration", smart_configuration_v1, name="smart_configuration"),
]

urlpatterns_v2 = [
    # accounts
    path("v2/accounts/", include("apps.accounts.v2.urls")),
    # authorization
    path("v2/o/", include("apps.authorization.v2.urls")),
    # connect/userinfo
    re_path(
        r"^v2/connect/userinfo",
        openidconnect_userinfo_v2,
        name="openid_connect_userinfo_v2",
    ),
    # dot_ext
    path("v2/o/", include("apps.dot_ext.v2.urls")),
    # fhir/bluebutton
    path("v2/fhir/", include("apps.fhir.bluebutton.v2.urls")),
    # fhir/metadata
    path("v2/fhir/metadata", fhir_conformance_v2, name="fhir_conformance_metadata_v2"),
    # openid_config
    path(
        "v2/connect/.well-known/openid-configuration", openid_configuration_v2, name="openid-configuration-v2"
    ),
    # smart config
    path("v2/fhir/.well-known/smart-configuration", smart_configuration_v2, name="smart_configuration"),
]

urlpatterns_v3 = [
    # accounts
    # TODO: This does not exist yet.
    # path("v3/accounts/", waffle_switch("v3_endpoints")(include("apps.accounts.v3.urls"))),
    # authorization
    path("v3/o/", include("apps.authorization.v3.urls")),
    # dot_ext
    path("v3/o/", include("apps.dot_ext.v3.urls")),
]

urlpatterns_v3 = urlpatterns_v3 + [
    # connect/userinfo
    re_path(
        r"^v3/connect/userinfo",
        waffle_switch('v3_endpoints')(openidconnect_userinfo_v3),
        name="openid_connect_userinfo_v3",
    ),
    # fhir/bluebutton
    path("v3/fhir/", include("apps.fhir.bluebutton.v3.urls")),
    # fhir/metadata
    path("v3/fhir/metadata", waffle_switch('v3_endpoints')(fhir_conformance_v3), name="fhir_conformance_metadata_v3"),
    # openid_config
    path(
        "v3/connect/.well-known/openid-configuration", waffle_switch('v3_endpoints')(openid_configuration_v3),
        name="openid-configuration-v3"
    ),
    # smart config
    path("v3/fhir/.well-known/smart-configuration",
         waffle_switch('v3_endpoints')(smart_configuration_v3),
         name="smart_configuration_v3"),
]

urlpatterns = all_versions + urlpatterns_v1 + urlpatterns_v2 + urlpatterns_v3

# If running in local development, add the media and static urls:
if settings.IS_MEDIA_URL_LOCAL is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if IsAppInstalled("apps.testclient"):
    urlpatterns += [
        path("testclient/", include("apps.testclient.urls")),
    ]

if IsAppInstalled("apps.mymedicare_cb"):
    urlpatterns += [
        path("mymedicare/", include("apps.mymedicare_cb.urls")),
    ]

if not getattr(settings, "NO_UI", False):
    urlpatterns += [
        path("", include("apps.home.urls")),
    ]

handler500 = "hhs_oauth_server.urls.server_error"
handler400 = "hhs_oauth_server.urls.bad_request"


# TODO Replace this with defaults from rest_framework once upgrated to > 3.7.7
def server_error(request, *args, **kwargs):
    """
    Generic 500 error handler.
    """
    data = {"error": "Server Error (500)"}
    return JsonResponse(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def bad_request(request, exception, *args, **kwargs):
    """
    Generic 400 error handler.
    """
    data = {"error": "Bad Request (400)"}
    return JsonResponse(data, status=status.HTTP_400_BAD_REQUEST)
