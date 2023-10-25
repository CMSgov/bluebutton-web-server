from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from apps.authorization.views import ExpireDataAccessGrantView, AuthorizedGrants, toggle_language
from waffle.decorators import waffle_switch

router = DefaultRouter()
router.register(r"tokens", AuthorizedGrants, basename="token")

urlpatterns = [
    path("", include((router.urls, "authorization"), namespace="token_management")),
    re_path(
        r"^expire_authenticated_user/(?P<patient_id>[\-0-9]+)/$",
        waffle_switch("expire_grant_endpoint")(ExpireDataAccessGrantView.as_view()),
        name="expire_access_grant",
    ),
    re_path(r"^toggle_language/$", toggle_language, name="toggle-language"),
]
