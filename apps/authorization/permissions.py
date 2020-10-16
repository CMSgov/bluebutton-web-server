from rest_framework import (permissions, exceptions)
from .models import DataAccessGrant


class DataAccessGrantPermission(permissions.BasePermission):
    """
    Permission check for a Grant related to the token used.
    """
    def has_permission(self, request, view):
        return DataAccessGrant.objects.filter(
            beneficiary=request.auth.user,
            application=request.auth.application,
        ).exists()

    def has_object_permission(self, request, view, obj):
        # Now check that the user has permission to access the data
        # Patient resources were taken care of above
        # Return 404 on error to avoid notifying unauthorized user the object exists

        return is_resource_for_patient(obj, request.crosswalk.fhir_id)


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
