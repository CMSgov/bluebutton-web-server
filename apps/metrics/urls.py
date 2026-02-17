from django.urls import include, path, re_path
from django.contrib import admin
from apps.metrics.views import (
    BeneMetricsView,
    AppMetricsView,
    AppMetricsDetailView,
    TokenMetricsView,
    DevelopersView,
    DevelopersStreamView,
    ArchivedTokenView,
    DataAccessGrantView,
    ArchivedDataAccessGrantView,
    CheckDataAccessGrantsView,
    CheckCrosswalksView,
)

admin.autodiscover()

urlpatterns = [
    path("beneficiaries", BeneMetricsView.as_view(), name="beneficiaries"),
    path(
        "applications/<int:pk>",
        AppMetricsDetailView.as_view(),
        name="applications-detail",
    ),
    path("applications/", AppMetricsView.as_view(), name="applications"),
    path("crosswalks/check", CheckCrosswalksView.as_view(), name="check-crosswalks"),
    path("developers/", DevelopersView.as_view(), name="developers"),
    path("tokens", TokenMetricsView.as_view(), name="tokens"),
    path("tokens/archive", ArchivedTokenView.as_view(), name="archived-tokens"),
    path("grants", DataAccessGrantView.as_view(), name="grants"),
    path(
        "grants/archive", ArchivedDataAccessGrantView.as_view(), name="archive-grants"
    ),
    path("grants/check", CheckDataAccessGrantsView.as_view(), name="check-grants"),
    path(
        "raw/",
        include(
            [
                re_path(r"^developers", DevelopersStreamView.as_view()),
            ]
        ),
    ),
]
