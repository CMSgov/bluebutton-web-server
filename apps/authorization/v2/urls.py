from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter
from apps.authorization.views import ExpireDataAccessGrantView, AuthorizedGrants
from waffle.decorators import waffle_switch

router = DefaultRouter()
router.register(r'tokens', AuthorizedGrants, basename='token')

urlpatterns = [
    url(r'', include((router.urls, 'authorization'), namespace='token_management_v2')),

    url(r'^expire_authenticated_user/(?P<patient_id>[\-0-9]+)/$',
        waffle_switch('expire_grant_endpoint')(ExpireDataAccessGrantView.as_view()),
        name='expire_access_grant'
    )
]
