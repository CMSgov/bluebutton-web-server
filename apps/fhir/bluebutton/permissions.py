import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import permissions, exceptions
from rest_framework.exceptions import AuthenticationFailed
from .constants import ALLOWED_RESOURCE_TYPES
from waffle import switch_is_active
from apps.constants import Versions, VersionNotMatched

import apps.logging.request_logger as bb2logging

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))

User = get_user_model()


class ResourcePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.resource_type not in ALLOWED_RESOURCE_TYPES:
            logger.info(
                "User requested read access to the %s resource type"
                % request.resource_type
            )
            raise exceptions.NotFound(
                "The requested resource type, %s, is not supported"
                % request.resource_type
            )

        return True


class HasCrosswalk(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.version in Versions.supported_versions():
            return request.user and request.user.crosswalk and request.user.crosswalk.fhir_id(view.version)
        else:
            # this should not happen where we'd get an unsupported version
            raise VersionNotMatched("Version not matched in has_permission")


class ReadCrosswalkPermission(HasCrosswalk):
    def has_object_permission(self, request, view, obj):
        # Now check that the user has permission to access the data
        # Patient resources were taken care of above # TODO - verify this
        # Return 404 on error to avoid notifying unauthorized user the object exists
        if view.version in Versions.supported_versions():
            fhir_id = request.crosswalk.fhir_id(view.version)
        else:
            raise VersionNotMatched()
        try:
            if request.resource_type == "Coverage":
                reference = obj["beneficiary"]["reference"]
                reference_id = reference.split("/")[1]
                # BB2-4166-TODO : this needs to use version to determine fhir_id, probably in request
                if reference_id != fhir_id:
                    raise exceptions.NotFound()
            elif request.resource_type == "ExplanationOfBenefit":
                reference = obj["patient"]["reference"]
                reference_id = reference.split("/")[1]
                # BB2-4166-TODO : this needs to use version to determine fhir_id, probably in request
                if reference_id != fhir_id:
                    raise exceptions.NotFound()
            else:
                reference_id = obj["id"]
                # BB2-4166-TODO : this needs to use version to determine fhir_id, probably in request
                if reference_id != fhir_id:
                    raise exceptions.NotFound()

        except exceptions.NotFound:
            raise
        except Exception:
            logger.exception("An error occurred fetching beneficiary id")
            return False
        return True


class SearchCrosswalkPermission(HasCrosswalk):
    def has_object_permission(self, request, view, obj):
        # BB2-4166-TODO: this is hardcoded to be version 2
        if switch_is_active('v3_endpoints'):
            patient_id = request.crosswalk.fhir_id(Versions.V3)
        else:
            patient_id = request.crosswalk.fhir_id(Versions.V2)

        if "patient" in request.GET and request.GET["patient"] != patient_id:
            return False

        if (
            "beneficiary" in request.GET
            and patient_id not in request.GET["beneficiary"]
        ):
            return False
        return True


class ApplicationActivePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        app_is_active = request.auth and request.auth.application.active
        app_name = (
            request.auth.application.name
            if request.auth and request.auth.application.name
            else "Unknown"
        )

        # Check for application enabled/active
        if app_is_active is False:
            # in order to generate application specific message, short circuit base
            # permission's error raise flow
            raise AuthenticationFailed(
                settings.APPLICATION_TEMPORARILY_INACTIVE.format(app_name)
            )

        return True
