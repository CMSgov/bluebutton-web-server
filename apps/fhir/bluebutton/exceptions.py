from rest_framework.exceptions import APIException
from rest_framework import status


class UpstreamServerException(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
