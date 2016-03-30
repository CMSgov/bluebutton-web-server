from ..models import SupportedResourceType
from ..utils import (kickout_404, kickout_403)



def check_access_interaction_and_resource_type(resource_type, interaction_type):
    try:
        rt = SupportedResourceType.objects.get(resource_name=resource_type)
        if interaction_type not in rt.get_supported_interaction_types():
            msg = "The interaction %s is not permitted on %s FHIR resources on this FHIR sever." % (interaction_type,
                                                                           resource_type)
            return kickout_403(msg)
    except SupportedResourceType.DoesNotExist:
        msg = "%s is not a supported resource type on this FHIR server." % (resource_type)
        return kickout_404(msg)
    return False