from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework import status
from django.urls import include, path, re_path
from django.contrib import admin
from apps.accounts.views.oauth2_profile import openidconnect_userinfo
from apps.fhir.bluebutton.views.home import fhir_conformance, fhir_conformance_v2
from apps.wellknown.views.openid import smart_configuration
from hhs_oauth_server.hhs_oauth_server_context import IsAppInstalled

admin.autodiscover()
admin.site.enable_nav_sidebar = False

ADMIN_REDIRECTOR = getattr(settings, "ADMIN_PREPEND_URL", "")


urlpatterns = [
    path("health", include("apps.health.urls")),
    re_path(r"^.well-known/", include("apps.wellknown.urls")),
    path("v1/fhir/.wellknown/smart-configuration", smart_configuration, name="smart_configuration"),
    path("forms/", include("apps.forms.urls")),
    path("v1/accounts/", include("apps.accounts.urls")),
    re_path(
        r"^v1/connect/userinfo", openidconnect_userinfo, name="openid_connect_userinfo"
    ),
    path("v1/fhir/metadata", fhir_conformance, name="fhir_conformance_metadata"),
    path("v1/fhir/", include("apps.fhir.bluebutton.urls")),
    path("v1/o/", include("apps.dot_ext.urls")),
    path("v1/o/", include("apps.authorization.urls")),
    path("v2/accounts/", include("apps.accounts.v2.urls")),
    re_path(
        r"^v2/connect/userinfo",
        openidconnect_userinfo,
        name="openid_connect_userinfo_v2",
    ),
    path("v2/fhir/.wellknown/smart-configuration", smart_configuration, name="smart_configuration"),
    path("v2/fhir/metadata", fhir_conformance_v2, name="fhir_conformance_metadata_v2"),
    path("v2/fhir/", include("apps.fhir.bluebutton.v2.urls")),
    path("v2/o/", include("apps.dot_ext.v2.urls")),
    path("v2/o/", include("apps.authorization.v2.urls")),
    path("docs/", include("apps.docs.urls")),
    re_path(r"^" + ADMIN_REDIRECTOR + "admin/metrics/", include("apps.metrics.urls")),
    re_path(r"^" + ADMIN_REDIRECTOR + "admin/", admin.site.urls),
    path("creds", include("apps.creds.urls")),
]

# If running in local development, add the media and static urls:
if settings.IS_MEDIA_URL_LOCAL is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if IsAppInstalled("apps.testclient"):
    urlpatterns += [
        path("testclient/", include("apps.testclient.urls")),
        path("myapp/", include("apps.testclient.urls4myapp")),
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
