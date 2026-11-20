import io
import sys
import traceback

from django.db.utils import IntegrityError
from rest_framework.exceptions import server_error
from rest_framework.views import exception_handler

from apps.logging.sensitive_logging_filters import mask_erroring_database_rows


def custom_exception_handler(exc, context):
    print('custom DRF exception handler hit')
    response = exception_handler(exc, context)

    if response is None:
        print('I found a None response to an exception')
    else:
        return response


class ProcessExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        print('I hit an exception')

        if isinstance(exception, IntegrityError):
            s = io.StringIO()
            traceback.print_exception(exception, file=s)
            print(mask_erroring_database_rows(s.getvalue()), file=sys.stderr)

            return server_error(request)

        return None  # default exception handling proceeds
