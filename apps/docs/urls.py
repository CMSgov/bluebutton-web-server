from django.urls import path
from .views import openapi
from .views import openapi_oauth2_redirect

urlpatterns = [
    path("openapi", openapi, name="bluebutton_openapi"),
    path("oauth2-redirect", openapi_oauth2_redirect, name="oauth2-redirect"),
]
