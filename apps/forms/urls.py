from django.urls import path

from . import views

urlpatterns = [
    path(
        "/interim-prod-access",
        views.interim_prod_access_view,
        name="new-interim-prod-access",
    ),
    path(
        "/interim-prod-access/<str:id>",
        views.interim_prod_access_view,
        name="existing-interim-prod-access",
    ),
]
