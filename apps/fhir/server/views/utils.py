from apps.fhir.server.models import SupportedResourceType
from apps.fhir.fhir_core.utils import (kickout_404, kickout_403)


# DONE: We need to deal with multiple resourceTypes - filter by FHIRServer?
def check_access_interaction_and_resource_type(resource_type,
                                               interaction_type,
                                               rr):
    try:
        rt = SupportedResourceType.objects.get(resourceType=resource_type,
                                               fhir_source=rr)
        if interaction_type not in rt.get_supported_interaction_types():
            msg = 'The interaction {} is not permitted ' \
                  'on {} FHIR resources ' \
                  'on this FHIR sever.'.format(interaction_type,
                                               resource_type)
            return kickout_403(msg)
    except SupportedResourceType.DoesNotExist:
        msg = '{} is not a supported ' \
              'resource type on this FHIR server.'.format(resource_type)
        return kickout_404(msg)
    return False
