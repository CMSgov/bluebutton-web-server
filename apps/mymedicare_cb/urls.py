from django.conf.urls import url
from .views import callback, mymedicare_login, mymedicare_choose_login
from django.views.generic import TemplateView

__author__ = "Alan Viars"

urlpatterns = [
    url(r'sls-callback$', callback, name='mymedicare-sls-callback'),
    url(r'choose-login$', mymedicare_choose_login,
        name='mymedicare-choose-login'),
    url(r'login$', mymedicare_login, name='mymedicare-login'),
    url(r'do-not-approve$', TemplateView.as_view(template_name='design_system/do-not-approve.html'),
        name='do_not_approve'),

]
