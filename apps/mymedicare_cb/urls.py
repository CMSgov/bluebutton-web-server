from django.conf.urls import url
from .views import callback, callback_v2, mymedicare_login, mymedicare_login_v2

urlpatterns = [
    url(r'sls-callback$', callback, name='mymedicare-sls-callback'),
    url(r'login$', mymedicare_login, name='mymedicare-login'),
    url(r'sls-callback-v2$', callback_v2, name='mymedicare-sls-callback-v2'),
    url(r'login-v2$', mymedicare_login_v2, name='mymedicare-login-v2'),
]
