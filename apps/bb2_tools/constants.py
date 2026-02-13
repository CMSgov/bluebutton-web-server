from apps.bb2_tools.models import (
    MyAccessTokenViewer,
    MyRefreshTokenViewer,
    MyArchivedTokenViewer,
)
from django.conf import settings

ADMIN_PREPEND = getattr(settings, 'ADMIN_PREPEND_URL', '')
BB2_TOOLS_PATH = (
    '/{}/admin/bb2_tools/'.format(ADMIN_PREPEND)
    if ADMIN_PREPEND
    else '/admin/bb2_tools/'
)

LINK_REF_FMT = "<a  href='{0}{1}?q={2}&user__id__exact={3}'>{4}</a>"
TOKEN_VIEWERS = {MyAccessTokenViewer, MyRefreshTokenViewer, MyArchivedTokenViewer}

CMS_SPLUNK_URL = "https://splunk.cloud.cms.gov"

# splunk dashboards links:
SPLUNK_DASHBOARDS = [
    {
        "display_name": "BB2 Authorization Flow Dashboard",
        "url": "{}/en-US/app/cms_bbapi_landing_app/bb2_authorization_flow_dashboard".format(
            CMS_SPLUNK_URL
        ),
    },
    {
        "display_name": "API Big Stats Dashboard - Structured",
        "url": "{}/en-US/app/cms_bbapi_landing_app/00_api_big_stats_dashboard__structured".format(
            CMS_SPLUNK_URL
        ),
    },
    {
        "display_name": "BB2 DASG Metrics Dashboard",
        "url": "{}/en-US/app/cms_bbapi_landing_app/BB2_DASG_Metrics_Dashboard".format(
            CMS_SPLUNK_URL
        ),
    },
    {
        "display_name": "BB2 V2 Activities Dashboard",
        "url": "{}/en-US/app/cms_bbapi_landing_app/bb2_v2_activities_dashboard".format(
            CMS_SPLUNK_URL
        ),
    },
]
