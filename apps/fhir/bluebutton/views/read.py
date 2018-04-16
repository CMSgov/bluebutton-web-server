import logging
from rest_framework import exceptions
from apps.fhir.bluebutton.utils import get_crosswalk
from apps.fhir.bluebutton.views.generic import FhirDataView

logger = logging.getLogger('hhs_server.%s' % __name__)


#####################################################################
# These functions are a stepping stone to a single class based view #
#####################################################################

class ReadView(FhirDataView):

    def validate_response(self, response):
        # Now check that the user has permission to access the data
        # Patient resources were taken care of above
        # Return 404 on error to avoid notifying unauthorized user the object exists
        try:
            if self.resource_type == 'Coverage':
                reference = response._json()['beneficiary']['reference']
                reference_id = reference.split('/')[1]
                if reference_id != self.crosswalk.fhir_id:
                    raise exceptions.NotFound()
            elif self.resource_type == 'ExplanationOfBenefit':
                reference = response._json()['patient']['reference']
                reference_id = reference.split('/')[1]
                if reference_id != self.crosswalk.fhir_id:
                    raise exceptions.NotFound()
        except Exception:
            logger.warning('An error occurred fetching beneficiary id')
            raise exceptions.NotFound()

    def check_resource_permission(self, request, resource_type, resource_id, **kwargs):
        crosswalk = get_crosswalk(request.resource_owner)

        # If the user isn't matched to a backend ID, they have no permissions
        if crosswalk is None:
            logger.info('Crosswalk for %s does not exist' % request.user)
            raise exceptions.PermissionDenied(
                'No access information was found for the authenticated user')

        if resource_type == 'Patient':
            # Error out in advance for non-matching Patient records.
            # Other records must hit backend to check permissions.
            if resource_id != crosswalk.fhir_id:
                raise exceptions.PermissionDenied(
                    'You do not have permission to access data on the requested patient')
        return crosswalk

    def build_parameters(self, *args, **kwargs):
        return {
            "_format": "json"
        }

    def build_url(self, resource_router, resource_type, resource_id, **kwargs):
        return resource_router.fhir_url + resource_type + "/" + resource_id + "/"
