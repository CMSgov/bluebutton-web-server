import logging

from django.contrib.auth import get_user_model
from oauth2_provider.models import get_application_model
from oauth2_provider.views.base import get_access_token_model
from rest_framework import exceptions, permissions
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.request import Request
from waffle import get_waffle_flag_model

from apps.capabilities.models import ProtectedCapability
from apps.constants import (
    APPLICATION_DOES_NOT_HAVE_V3_ENABLED_YET,
    APPLICATION_DOES_NOT_HAVE_VALID_SCOPES,
    APPLICATION_TEMPORARILY_INACTIVE,
    FHIR_RES_TYPE_EOB,
    HHS_SERVER_LOGNAME_FMT,
)
from apps.fhir.constants import ALLOWED_RESOURCE_TYPES
from apps.utils import is_valid_scope
from apps.versions import VersionNotMatched, Versions

logger = logging.getLogger(HHS_SERVER_LOGNAME_FMT.format(__name__))

User = get_user_model()


class ResourcePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.resource_type not in ALLOWED_RESOURCE_TYPES:
            logger.info('User requested read access to the %s resource type' % request.resource_type)
            raise exceptions.NotFound('The requested resource type, %s, is not supported' % request.resource_type)

        return True


class HasCrosswalk(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.version in Versions.supported_versions():
            return request.user and request.user.crosswalk and request.user.crosswalk.fhir_id(view.version)
        else:
            # this should not happen where we'd get an unsupported version
            raise VersionNotMatched('Version not matched in has_permission')


class ReadCrosswalkPermission(HasCrosswalk):
    def has_object_permission(self, request, view, obj):
        # Now check that the user has permission to access the data
        # Patient resources were taken care of above # TODO - verify this
        # Return 404 on error to avoid notifying unauthorized user the object exists
        if view.version in Versions.supported_versions():
            fhir_id = request.crosswalk.fhir_id(view.version)
        else:
            raise VersionNotMatched('Version not matched in has_object_permission in ReadCrosswalkPermission')
        try:
            if request.resource_type == 'Coverage':
                reference = obj['beneficiary']['reference']
                reference_id = reference.split('/')[1]
                if reference_id != fhir_id:
                    raise exceptions.NotFound()
            elif request.resource_type == 'ExplanationOfBenefit':
                reference = obj['patient']['reference']
                reference_id = reference.split('/')[1]
                if reference_id != fhir_id:
                    raise exceptions.NotFound()
            else:
                reference_id = obj['id']
                if reference_id != fhir_id:
                    raise exceptions.NotFound()

        except exceptions.NotFound:
            raise
        except Exception:
            logger.exception('An error occurred fetching beneficiary id')
            return False
        return True


class SearchCrosswalkPermission(HasCrosswalk):
    def has_object_permission(self, request, view, obj) -> bool:  # type: ignore
        if view.version in Versions.supported_versions():
            patient_id = request.crosswalk.fhir_id(view.version)
        else:
            raise VersionNotMatched('Version not matched in has_object_permission in SearchCrosswalkPermission')
        if 'patient' in request.GET and request.GET['patient'] != patient_id:
            return False

        if 'beneficiary' in request.GET and patient_id not in request.GET['beneficiary']:
            return False
        return True


class ApplicationActivePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        app_is_active = request.auth and request.auth.application.active
        app_name = request.auth.application.name if request.auth and request.auth.application.name else 'Unknown'

        # Check for application enabled/active
        if app_is_active is False:
            # in order to generate application specific message, short circuit base
            # permission's error raise flow
            raise AuthenticationFailed(APPLICATION_TEMPORARILY_INACTIVE.format(app_name))

        return True


class V3EarlyAdopterPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # if it is not version 3, we do not need to check the waffle switch or flag
        if view.version < Versions.V3:
            return True

        token = get_access_token_model().objects.get(token=request._auth)
        application = get_application_model().objects.get(id=token.application_id)
        application_user = get_user_model().objects.get(id=application.user_id)
        flag = get_waffle_flag_model().get('v3_early_adopter')

        if flag.id is None or flag.is_active_for_user(application_user):
            return True
        else:
            raise PermissionDenied(APPLICATION_DOES_NOT_HAVE_V3_ENABLED_YET.format(application.name))


class AppScopePermission(permissions.BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        """
        Determines if the user/app has permission to make the call it's trying to make. Takes care of the
        case where a user/app goes through a v1/v2 auth flow and tries to make a v3 call that it's not authorized to make.

        args:
          - request: The API Request
          - view: The view
        returns:
          - True if there is a match with the current request and the scopes the app has in the database
          - Raises a custom 403 Forbidden error if not
        """
        # if it is not version 3, we do not need to check the scopes
        if view.version < Versions.V3:
            return True
        token = get_access_token_model().objects.get(token=request._auth)
        token_app_id = token.application_id
        if not token or not token_app_id:
            return False
        application_scopes = list(
            ProtectedCapability.objects.filter(application=token.application_id)
            .values_list('protected_resources', flat=True)
            .distinct()
        )
        is_valid = is_valid_scope(application_scopes, request)
        if not is_valid:
            raise PermissionDenied(
                APPLICATION_DOES_NOT_HAVE_VALID_SCOPES.format(token.application, request.resource_type)
            )
        return is_valid


class V2ExplanationOfBenefitPermission(permissions.BasePermission):
    """
    Global permission check that the request is either:
    1. not an EOB call
    2. v3 (in which case SAMHSA filtering will occur)
    3. for a token with no AccessTokenExtension (to allow older tokens to continue to work)
    4. for a token/extension with include_samhsa==True
    """

    def has_permission(self, request, view):
        if view.resource_type != FHIR_RES_TYPE_EOB:
            return True

        if view.version == Versions.V3:
            return True

        token = get_access_token_model().objects.get(token=request.auth)

        try:
            extension = token.accesstokenextension
        except get_access_token_model().accesstokenextension.RelatedObjectDoesNotExist:
            return True

        return extension.include_samhsa
