from django.conf.urls import url
from django.contrib import admin
from django.views.generic import TemplateView
from .views import authenticated_home

admin.autodiscover()

urlpatterns = [
    url(r'about',
        TemplateView.as_view(template_name='about_0.html'),
        name='about'),
    url(r'',
        authenticated_home,
        name='auth_home'),

]
