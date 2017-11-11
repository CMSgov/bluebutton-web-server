import logging

from django.views.decorators.csrf import csrf_exempt

from ..opoutcome_utils import kickout_400
from apps.fhir.bluebutton.views.read import read

logger = logging.getLogger('hhs_server.%s' % __name__)
logger_error = logging.getLogger('hhs_server_error.%s' % __name__)
logger_debug = logging.getLogger('hhs_server_debug.%s' % __name__)
logger_info = logging.getLogger('hhs_server_info.%s' % __name__)

DF_EXTRA_INFO = False


@csrf_exempt
def read_or_update_or_delete(request, resource_type, id):
    """
    Route to read, update, or delete based on HTTP method FHIR Interaction
    """

    if request.method == 'GET':
        # Read
        logger.debug("making read with Resource:"
                     "%s and id:%s" % (resource_type, id))
        return read(request, resource_type, id)
    # elif request.method == 'PUT':
    #     # update
    #     return update(request, resource_type, id)
    # elif request.method == 'DELETE':
    #     # delete
    #     return delete(request, resource_type, id)
    # else:
    # Not supported.
    msg = "HTTP method %s not supported at this URL." % (request.method)
    # logger_info.info(msg)
    logger.debug(msg)

    return kickout_400(msg)
