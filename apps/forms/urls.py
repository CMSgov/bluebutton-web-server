from django.urls import path
from waffle.decorators import waffle_switch

from .views import InterimProdAccessView

urlpatterns = [
    path(
        "interim-prod-access",
        waffle_switch("interim-prod-access")(InterimProdAccessView.as_view()),
        name="interim-prod-access",
    )
]
