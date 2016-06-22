from django.views.generic import TemplateView
from django.conf.urls import url


urlpatterns = [
    url(r'^learn/0/$', TemplateView.as_view(template_name='education_0.html'), name='learn_0'),
    url(r'^learn/1/$', TemplateView.as_view(template_name='education_1.html'), name='learn_1'),
    url(r'^learn/2/$', TemplateView.as_view(template_name='education_2.html'), name='learn_2'),
]
