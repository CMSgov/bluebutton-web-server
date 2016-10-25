from django.conf.urls import url
from django.contrib import admin
from django.views.generic import TemplateView
from .views import authenticated_home

admin.autodiscover()

urlpatterns = [
    url(r'about',
        TemplateView.as_view(template_name='about_0.html'),
        name='about'),
    url(r'help_developer',
        TemplateView.as_view(template_name='help_developer_0.html'),
        name='help_developer'),
    url(r'help',
        TemplateView.as_view(template_name='help_user_0.html'),
        name='help_user'),
    url(r'',
        authenticated_home,
        name='auth_home'),

]
