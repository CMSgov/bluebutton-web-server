from django.conf.urls import url
# from django.views.generic import TemplateView
from .views import authenticated_home


urlpatterns = [
    url(r'', authenticated_home, name='home'),

]
