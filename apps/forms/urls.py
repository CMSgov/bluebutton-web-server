from django.urls import path

from .views import InterimProdAccessView

urlpatterns = [
    path(
        "interim-prod-access",
        InterimProdAccessView.as_view(),
        name="interim-prod-access",
    )
]
