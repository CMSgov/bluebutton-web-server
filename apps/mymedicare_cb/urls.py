from django.conf.urls import url
from django.views.generic import TemplateView
from .views import callback, mymedicare_login

__author__ = "Alan Viars"

urlpatterns = [
    url(r'sls-callback$', callback, name='mymedicare-sls-callback'),
    url(r'login$', mymedicare_login, name='mymedicare-login'),
    url(r'$', TemplateView.as_view(template_name='design_system/sample.html')),

]
