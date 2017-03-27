from django.conf.urls import url
from .views import openid_configuration


urlpatterns = [
    # openid-configuration -----------------------------------
    url(r'^openid-configuration$',
        openid_configuration,
        name='openid-configuration'),
]
