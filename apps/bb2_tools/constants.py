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
