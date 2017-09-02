import logging

from django.contrib.auth.decorators import login_required

from apps.dot_ext.decorators import capability_protected_resource

from apps.fhir.bluebutton.views.read import generic_read
# from apps.fhir.bluebutton.views.search import read_search


logger = logging.getLogger('hhs_server.%s' % __name__)

DF_EXTRA_INFO = False


@login_required()
def history(request, resource_type, r_id, *args, **kwargs):
    """
    Read from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """

    interaction_type = '_history'
    history = generic_read(request,
                           interaction_type,
                           resource_type,
                           id=id,
                           via_oauth=False,
                           *args,
                           **kwargs)
    return history


@capability_protected_resource()
def oauth_history(request, resource_type, id, *args, **kwargs):
    """
    Read from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """

    interaction_type = '_history'
    history = generic_read(request,
                           interaction_type,
                           resource_type,
                           id=id,
                           via_oauth=True,
                           *args,
                           **kwargs)
    return history
