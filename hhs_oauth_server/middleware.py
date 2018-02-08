from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import APIException
from django.http import HttpResponse


# Mixin for compatibility with Django <1.10
class HandleAPIExceptionMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, APIException):
            return HttpResponse(content=exception.detail,
                                status=exception.get_codes())
