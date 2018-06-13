import logging
from rest_framework import (permissions, exceptions)
from .constants import ALLOWED_RESOURCE_TYPES
from .utils import get_crosswalk
from ..server.authentication import authenticate_crosswalk

logger = logging.getLogger('hhs_server.%s' % __name__)


class ResourcePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.resource_type not in ALLOWED_RESOURCE_TYPES:
            logger.info('User requested read access to the %s resource type' % request.resource_type)
            raise exceptions.NotFound('The requested resource type, %s, is not supported' % request.resource_type)

        return True


class HasCrosswalk(permissions.BasePermission):

    def has_permission(self, request, view):
        crosswalk = get_crosswalk(request.resource_owner)

        # If the user isn't matched to a backend ID, they have no permissions
        if crosswalk is None:
            logger.info('Crosswalk for %s does not exist' % request.user)
            return False

        if crosswalk.fhir_id == "":
            authenticate_crosswalk(crosswalk)

        request.crosswalk = crosswalk

        return True


class ReadCrosswalkPermission(HasCrosswalk):

    def has_object_permission(self, request, view, obj):
        # Now check that the user has permission to access the data
        # Patient resources were taken care of above
        # Return 404 on error to avoid notifying unauthorized user the object exists

        try:
            if request.resource_type == 'Coverage':
                reference = obj['beneficiary']['reference']
                reference_id = reference.split('/')[1]
                if reference_id != request.crosswalk.fhir_id:
                    raise exceptions.NotFound()
            elif request.resource_type == 'ExplanationOfBenefit':
                reference = obj['patient']['reference']
                reference_id = reference.split('/')[1]
                if reference_id != request.crosswalk.fhir_id:
                    raise exceptions.NotFound()
            else:
                reference_id = obj['id']
                if reference_id != request.crosswalk.fhir_id:
                    raise exceptions.NotFound()

        except exceptions.NotFound:
            raise
        except Exception:
            logger.exception('An error occurred fetching beneficiary id')
            return False
        return True


class SearchCrosswalkPermission(HasCrosswalk):

    def has_object_permission(self, request, view, obj):
        patient_id = request.crosswalk.fhir_id

        if 'patient' in request.GET and request.GET['patient'] != patient_id:
            return False

        if 'beneficiary' in request.GET and patient_id not in request.GET['beneficiary']:
            return False
        return True
