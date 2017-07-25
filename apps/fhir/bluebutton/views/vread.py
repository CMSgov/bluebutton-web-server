import logging

from apps.fhir.bluebutton.views.read import generic_read
# from apps.fhir.bluebutton.views.search import read_search

logger = logging.getLogger('hhs_server.%s' % __name__)
logger_error = logging.getLogger('hhs_server_error.%s' % __name__)
logger_debug = logging.getLogger('hhs_server_debug.%s' % __name__)
logger_info = logging.getLogger('hhs_server_info.%s' % __name__)

DF_EXTRA_INFO = False


def vread(request, resource_type, r_id, *args, **kwargs):
    """
    Read from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """
    interaction_type = 'vread'
    vread = generic_read(request,
                         interaction_type,
                         resource_type,
                         rt_id=r_id,
                         *args,
                         **kwargs)
    return vread
