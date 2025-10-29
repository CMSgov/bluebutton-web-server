from django.conf import settings
from rest_framework import (permissions, exceptions)
from apps.constants import Versions, VersionNotMatched

from .models import DataAccessGrant


class DataAccessGrantPermission(permissions.BasePermission):
    """
    Permission check for a Grant related to the token used.
    """
    def has_permission(self, request, view):
        dag = None
        try:
            dag = DataAccessGrant.objects.get(
                beneficiary=request.auth.user,
                application=request.auth.application
            )
        except DataAccessGrant.DoesNotExist:
            return False

        if dag:
            if dag.has_expired():
                raise exceptions.NotAuthenticated(
                    settings.APPLICATION_THIRTEEN_MONTH_DATA_ACCESS_EXPIRED_MESG
                )
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Now check that the user has permission to access the data
        # Patient resources were taken care of above
        # Return 404 on error to avoid notifying unauthorized user the object exists

        # BB2-4166-TODO: this is hardcoded to be version 2
        # TODO: The use of view.version is not always going to be right. There are several
        # ways where we reference versions and this would need a spike ticket to understand properly.
        if view.version in Versions.supported_versions():
            return is_resource_for_patient(obj, request.crosswalk.fhir_id(view.version))
        else:
            raise VersionNotMatched()


def is_resource_for_patient(obj, patient_id):
    try:
        if obj['resourceType'] == 'Coverage':
            reference = obj['beneficiary']['reference']
            reference_id = reference.split('/')[1]
            if reference_id != patient_id:
                raise exceptions.NotFound()
        elif obj['resourceType'] == 'ExplanationOfBenefit':
            reference = obj['patient']['reference']
            reference_id = reference.split('/')[1]
            if reference_id != patient_id:
                raise exceptions.NotFound()
        elif obj['resourceType'] == 'Patient':
            reference_id = obj['id']
            if reference_id != patient_id:
                raise exceptions.NotFound()
        elif obj['resourceType'] == 'Bundle':
            for entry in obj.get('entry', []):
                is_resource_for_patient(entry['resource'], patient_id)
        else:
            raise exceptions.NotFound()

    except exceptions.NotFound:
        raise
    except Exception:
        return False
    return True
