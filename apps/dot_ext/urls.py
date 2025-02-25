from django.urls import path, re_path
from oauth2_provider import views as oauth2_views
from . import views


app_name = "oauth2_provider"


base_urlpatterns = [
    path("authorize/", views.AuthorizationView.as_view(version=2), name="authorize"),
    re_path(
        r"^authorize/(?P<uuid>[\w-]+)/$",
        views.ApprovalView.as_view(),
        name="authorize-instance",
    ),
    path("token/", views.TokenView.as_view(), name="token"),
    path("revoke_token/", views.RevokeTokenView.as_view(), name="revoke-token"),
    path("revoke/", views.RevokeView.as_view(), name="revoke"),
    path("introspect/", views.IntrospectTokenView.as_view(), name="introspect"),
]


management_urlpatterns = [
    # Application management views
    path("applications/", oauth2_views.ApplicationList.as_view(), name="list"),
    path(
        "applications/register/",
        views.ApplicationRegistration.as_view(),
        name="register",
    ),
    re_path(
        r"^applications/(?P<pk>[\w-]+)/$",
        oauth2_views.ApplicationDetail.as_view(),
        name="detail",
    ),
    re_path(
        r"^applications/(?P<pk>[\w-]+)/delete/$",
        views.ApplicationDelete.as_view(),
        name="delete",
    ),
    re_path(
        r"^applications/(?P<pk>[\w-]+)/update/$",
        views.ApplicationUpdate.as_view(),
        name="update",
    ),
    # Token management views
    path(
        "authorized_tokens/",
        oauth2_views.AuthorizedTokensListView.as_view(),
        name="authorized-token-list",
    ),
    re_path(
        r"^authorized_tokens/(?P<pk>[\w-]+)/delete/$",
        oauth2_views.AuthorizedTokenDeleteView.as_view(),
        name="authorized-token-delete",
    ),
]


urlpatterns = base_urlpatterns + management_urlpatterns
