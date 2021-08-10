from django.conf.urls import url

from .views import (
    login_page,
    login,
    token,
    userinfo,
    signout,
    health,
)

urlpatterns = [
    # path('admin/', admin.site.urls),
    # mslsx end points
    url(r'^sso/authorize\\?.+', login_page),
    url(r'^login/', login),
    url(r'^health$', health),
    url(r'^sso/session', token),
    url(r'^v1/users/', userinfo),
    url(r'^sso/signout', signout),
]
