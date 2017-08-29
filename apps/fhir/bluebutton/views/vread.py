import logging

from django.contrib.auth.decorators import login_required

from apps.dot_ext.decorators import capability_protected_resource
from apps.fhir.bluebutton.views.read import generic_read
# from apps.fhir.bluebutton.views.search import read_search

logger = logging.getLogger('hhs_server.%s' % __name__)
logger_error = logging.getLogger('hhs_server_error.%s' % __name__)
logger_debug = logging.getLogger('hhs_server_debug.%s' % __name__)
logger_info = logging.getLogger('hhs_server_info.%s' % __name__)

DF_EXTRA_INFO = False


@login_required()
def vread(request, resource_type, id, *args, **kwargs):
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
                         via_oauth=False,
                         *args,
                         **kwargs)
    return vread


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
