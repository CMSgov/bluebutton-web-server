from django.urls import path, re_path
from oauth2_provider import views as oauth2_views
from waffle.decorators import waffle_switch

from apps.dot_ext import views


app_name = "oauth2_provider_v3"


base_urlpatterns = [
    path("authorize/", waffle_switch("v3_endpoints")(views.AuthorizationView.as_view(version=3)), name="authorize-v3"),
    re_path(
        r"^authorize/(?P<uuid>[\w-]+)/$",
        waffle_switch("v3_endpoints")(views.ApprovalView.as_view(version=3)),
        name="authorize-instance-v3",
    ),
    path("token/", waffle_switch("v3_endpoints")(views.TokenView.as_view()), name="token-v3"),
    path("revoke_token/", waffle_switch("v3_endpoints")(views.RevokeTokenView.as_view()), name="revoke-token-v3"),
    path("revoke/", waffle_switch("v3_endpoints")(views.RevokeView.as_view()), name="revoke-v3"),
    path("introspect/", waffle_switch("v3_endpoints")(views.IntrospectTokenView.as_view()), name="introspect-v3"),
]


management_urlpatterns = [
    # Application management views
    path("applications/", waffle_switch("v3_endpoints")(oauth2_views.ApplicationList.as_view()), name="list-v3"),
    path(
        "applications/register/",
        waffle_switch("v3_endpoints")(views.ApplicationRegistration.as_view()),
        name="register-v3",
    ),
    re_path(
        r"^applications/(?P<pk>[\w-]+)/$",
        waffle_switch("v3_endpoints")(oauth2_views.ApplicationDetail.as_view()),
        name="detail-v3",
    ),
    re_path(
        r"^applications/(?P<pk>[\w-]+)/delete/$",
        waffle_switch("v3_endpoints")(views.ApplicationDelete.as_view()),
        name="delete-v3",
    ),
    re_path(
        r"^applications/(?P<pk>[\w-]+)/update/$",
        waffle_switch("v3_endpoints")(views.ApplicationUpdate.as_view()),
        name="update-v3",
    ),
    # Token management views
    path(
        "authorized_tokens/",
        waffle_switch("v3_endpoints")(oauth2_views.AuthorizedTokensListView.as_view()),
        name="authorized-token-list-v3",
    ),
    re_path(
        r"^authorized_tokens/(?P<pk>[\w-]+)/delete/$",
        waffle_switch("v3_endpoints")(oauth2_views.AuthorizedTokenDeleteView.as_view()),
        name="authorized-token-delete-v3",
    ),
]


urlpatterns = base_urlpatterns + management_urlpatterns
