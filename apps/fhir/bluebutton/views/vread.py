from apps.dot_ext.decorators import capability_protected_resource
from apps.fhir.bluebutton.views.read import generic_read

DF_EXTRA_INFO = False


@capability_protected_resource()
def oauth_vread(request, resource_type, id, *args, **kwargs):
    """
    Read from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """
    interaction_type = 'vread'
    vread = generic_read(request,
                         interaction_type,
                         resource_type,
                         id=id,
                         via_oauth=True,
                         *args,
                         **kwargs)
    return vread
