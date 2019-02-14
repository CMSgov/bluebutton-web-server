import logging
from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework.response import Response
from .checks import services

logger = logging.getLogger('hhs_server.%s' % __name__)


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'


class Check(APIView):

    def get(self, request, format=None):
        try:
            for check in services:
                if not check():
                    raise ServiceUnavailable()
        except ServiceUnavailable:
            raise
        except Exception:
            logger.exception("health check raised exception")
            raise ServiceUnavailable()

        return Response({'message': 'all\'s well'})
