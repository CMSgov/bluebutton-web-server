from django.conf.urls import url
from .views import callback, mymedicare_login, mymedicare_choose_login

__author__ = "Alan Viars"

urlpatterns = [
    url(r'sls-callback$', callback, name='mymedicare-sls-callback'),
    url(r'choose-login$', mymedicare_choose_login,
        name='mymedicare-choose-login'),
    url(r'login$', mymedicare_login, name='mymedicare-login'),

]
