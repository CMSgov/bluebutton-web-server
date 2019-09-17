from django.conf.urls import include, url
from oauth2_provider import views as oauth2_views
from . import views


app_name = "oauth2_provider"


base_urlpatterns = [
    url(r'^authorize/$', views.AuthorizationView.as_view(), name="authorize"),
    url(r'^authorize/(?P<uuid>[\w-]+)/$', views.ApprovalView.as_view(), name="authorize-instance"),
    url(r"^token/$", oauth2_views.TokenView.as_view(), name="token"),
    url(r"^revoke_token/$", oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
    url(r"^introspect/$", oauth2_views.IntrospectTokenView.as_view(), name="introspect"),
]


management_urlpatterns = [
    # Application management views
    url(r"^applications/$", oauth2_views.ApplicationList.as_view(), name="list"),
    url(r"^applications/register/$", views.ApplicationRegistration.as_view(), name="register"),
    url(r"^applications/(?P<pk>[\w-]+)/$", oauth2_views.ApplicationDetail.as_view(), name="detail"),
    url(r"^applications/(?P<pk>[\w-]+)/delete/$", views.ApplicationDelete.as_view(), name="delete"),
    url(r"^applications/(?P<pk>[\w-]+)/update/$", views.ApplicationUpdate.as_view(), name="update"),
    # Token management views
    url(r"^authorized_tokens/$", oauth2_views.AuthorizedTokensListView.as_view(), name="authorized-token-list"),
    url(r"^authorized_tokens/(?P<pk>[\w-]+)/delete/$", oauth2_views.AuthorizedTokenDeleteView.as_view(),
        name="authorized-token-delete"),
]


urlpatterns = base_urlpatterns + management_urlpatterns
