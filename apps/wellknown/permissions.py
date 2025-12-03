import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from oauth2_provider.views.base import get_access_token_model
from oauth2_provider.models import get_application_model
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from waffle import get_waffle_flag_model
from apps.versions import Versions

import apps.logging.request_logger as bb2logging

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))


class V3EarlyAdopterWellKnownPermission(permissions.BasePermission):
    # BB2-4250: Handling to ensure this only returns successfully if the flag is enabled for the application
    # associated with the user making the call
    def has_permission(self, request, view):
        version = view.kwargs.get('version')
        # if it is not version 3, we do not need to check the waffle switch or flag
        if version < Versions.V3:
            return True

        token = get_access_token_model().objects.get(token=request._auth)
        application = get_application_model().objects.get(id=token.application_id)
        application_user = get_user_model().objects.get(id=application.user_id)
        flag = get_waffle_flag_model().get('v3_early_adopter')

        if flag.id is None or flag.is_active_for_user(application_user):
            return True
        else:
            raise PermissionDenied(
                settings.APPLICATION_DOES_NOT_HAVE_V3_ENABLED_YET.format(application.name)
            )
