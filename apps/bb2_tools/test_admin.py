from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.admin.sites import AdminSite

from apps.bb2_tools.admin import BeneficiaryDashboardAdmin
from apps.bb2_tools.models import (
    BeneficiaryDashboard,
    MyAccessTokenViewer,
    MyArchivedTokenViewer,
    MyRefreshTokenViewer,
)


def _mock_token_counts(filter_mock, rows):
    filter_mock.return_value.values.return_value.annotate.return_value = rows


def test_connected_application_names_are_html_escaped():
    application_names = {
        1: '<img src=x onerror=alert(document.domain)>',
        2: 'Ordinary App & Partners',
        3: '<svg/onload=alert(1)>',
        4: '<script>alert(1)</script>',
    }
    application_model = MagicMock()
    application_model.objects.get.side_effect = lambda id: SimpleNamespace(name=application_names[id])

    with (
        patch.object(MyAccessTokenViewer.objects, 'filter') as access_filter,
        patch.object(MyRefreshTokenViewer.objects, 'filter') as refresh_filter,
        patch.object(MyArchivedTokenViewer.objects, 'filter') as archived_filter,
        patch('apps.bb2_tools.admin.get_application_model', return_value=application_model),
    ):
        _mock_token_counts(
            access_filter,
            [
                {'application': 1, 'token_count': 1},
                {'application': 2, 'token_count': 2},
            ],
        )
        _mock_token_counts(refresh_filter, [{'application': 3, 'token_count': 3}])
        _mock_token_counts(archived_filter, [{'application': 4, 'token_count': 4}])

        rendered = BeneficiaryDashboardAdmin(
            BeneficiaryDashboard,
            AdminSite(),
        ).get_connected_applications(SimpleNamespace(user_id=123))

    assert str(rendered) == (
        '<div><ul>'
        '<li>App:&lt;img src=x onerror=alert(document.domain)&gt;, Token Count:1</li>'
        '<li>App:Ordinary App &amp; Partners, Token Count:2</li>'
        '<li>App:&lt;svg/onload=alert(1)&gt;, Refresh Token Count:3</li>'
        '<li>App:&lt;script&gt;alert(1)&lt;/script&gt;, Archived Token Count:4</li>'
        '</ul></div>'
    )
