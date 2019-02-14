from django.conf.urls import url
from .views import openid_configuration


urlpatterns = [
    # This should be deprecated or actuall support OIDC.
    # openid-configuration ----------------------------
    url(r'^openid-configuration$',
        openid_configuration,
        name='openid-configuration'),

    url(r'^oauth-authorization-server$',
        openid_configuration,
        name='oauth-authorization-server'),
]
