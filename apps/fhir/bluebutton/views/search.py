import logging

from django.views.decorators.csrf import csrf_exempt

from apps.fhir.fhir_core.utils import kickout_400
from apps.fhir.bluebutton.views.read import generic_read
from apps.fhir.bluebutton.views.home import fhir_conformance

logger = logging.getLogger('hhs_server.%s' % __name__)

DF_EXTRA_INFO = False


@csrf_exempt
def search_simple(request, resource_type):
    """Route to search FHIR Interaction"""

    if request.method == 'GET':
        # Search
        return generic_read(request, resource_type, id)
    # elif request.method == 'PUT':
    #     # update
    #     return update(request, resource_type, id)
    # elif request.method == 'DELETE':
    #     # delete
    #     return delete(request, resource_type, id)
    # else:
    # Not supported.
    msg = "HTTP method %s not supported at this URL." % (request.method)
    return kickout_400(msg)


def search(request, resource_type, *args, **kwargs):
    """
    Search from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/
    """

    interaction_type = 'search'

    logger.debug("Received:%s" % resource_type)

    conformance = False
    if resource_type is None:
        conformance = True
    elif resource_type.lower() == 'metadata':
        conformance = True
    elif resource_type.lower == 'conformance':
        conformance = True

    if conformance:
        return fhir_conformance(request, resource_type, *args, **kwargs)

    logger.debug("Interaction:%s. "
                 "Calling generic_read for %s" % (interaction_type,
                                                  resource_type))

    search = generic_read(request,
                          interaction_type,
                          resource_type,
                          id,
                          *args,
                          **kwargs)
    return search
