from django.conf.urls import include, url
from django.contrib import admin
from .views import (
    BeneMetricsView,
    AppMetricsView,
    AppMetricsDetailView,
    TokenMetricsView,
    DevelopersView,
    DevelopersStreamView,
    ArchivedTokenView,
    DataAccessGrantView,
)

admin.autodiscover()

urlpatterns = [
    url(r'^beneficiaries$', BeneMetricsView.as_view(), name='beneficiaries'),
    url(r'^applications/(?P<pk>\d+)$', AppMetricsDetailView.as_view(), name='applications-detail'),
    url(r'^applications/$', AppMetricsView.as_view(), name='applications'),
    url(r'^developers/$', DevelopersView.as_view(), name='developers'),
    url(r'^tokens$', TokenMetricsView.as_view(), name='tokens'),
    url(r'^tokens/archive$', ArchivedTokenView.as_view(), name='archived-tokens'),
    url(r'^grants$', DataAccessGrantView.as_view(), name='grants'),
    url(r'^raw/', include([
        url(r'^developers', DevelopersStreamView.as_view()),
    ]))
]
