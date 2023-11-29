from django.urls import path
from .views import openapi

urlpatterns = [
    path("openapi", openapi, name="bluebutton_openapi"),
]
