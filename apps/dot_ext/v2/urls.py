from django.urls import path, re_path
from oauth2_provider import views as oauth2_views
from apps.dot_ext import views


app_name = "oauth2_provider_v2"


base_urlpatterns = [
    path("authorize/", views.AuthorizationView.as_view(version=2), name="authorize-v2"),
    re_path(
        r"^authorize/(?P<uuid>[\w-]+)/$",
        views.ApprovalView.as_view(version=2),
        name="authorize-instance-v2",
    ),
    re_path(r"^token/?$", views.TokenView.as_view(), name="token-v2"),
    path("revoke_token/", views.RevokeTokenView.as_view(), name="revoke-token-v2"),
    path("revoke/", views.RevokeView.as_view(), name="revoke-v2"),
    path("introspect/", views.IntrospectTokenView.as_view(), name="introspect-v2"),
]


management_urlpatterns = [
    # Application management views
    path("applications/", oauth2_views.ApplicationList.as_view(), name="list-v2"),
    path(
        "applications/register/",
        views.ApplicationRegistration.as_view(),
        name="register-v2",
    ),
    re_path(
        r"^applications/(?P<pk>[\w-]+)/$",
        oauth2_views.ApplicationDetail.as_view(),
        name="detail-v2",
    ),
    re_path(
        r"^applications/(?P<pk>[\w-]+)/delete/$",
        views.ApplicationDelete.as_view(),
        name="delete-v2",
    ),
    re_path(
        r"^applications/(?P<pk>[\w-]+)/update/$",
        views.ApplicationUpdate.as_view(),
        name="update-v2",
    ),
    # Token management views
    path(
        "authorized_tokens/",
        oauth2_views.AuthorizedTokensListView.as_view(),
        name="authorized-token-list-v2",
    ),
    re_path(
        r"^authorized_tokens/(?P<pk>[\w-]+)/delete/$",
        oauth2_views.AuthorizedTokenDeleteView.as_view(),
        name="authorized-token-delete-v2",
    ),
]


urlpatterns = base_urlpatterns + management_urlpatterns
