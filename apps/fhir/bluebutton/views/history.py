import logging

from apps.fhir.bluebutton.views.read import generic_read


logger = logging.getLogger('hhs_server.%s' % __name__)

DF_EXTRA_INFO = False


def history(request, resource_type, id, *args, **kwargs):
    """
    Read from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """

    interaction_type = '_history'
    history = generic_read(request, interaction_type, resource_type, id, *args, **kwargs)
    return history
