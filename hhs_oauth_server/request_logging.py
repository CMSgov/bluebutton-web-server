import logging
import datetime
import uuid

logger = logging.getLogger('performance.%s' % __name__)

##############################################################################
#
# Request time logging middleware
# https://djangosnippets.org/snippets/1826/
#
##############################################################################


class RequestTimeLoggingMiddleware(object):
    """Middleware class logging request time to stderr.

    This class can be used to measure time of request processing
    within Django.  It can be also used to log time spent in
    middleware and in view itself, by putting middleware multiple
    times in INSTALLED_MIDDLEWARE.

    Static method `log_message' may be used independently of the
    middleware itself, outside of it, and even when middleware is not
    listed in INSTALLED_MIDDLEWARE.
    """

    @staticmethod
    def log_message(request, tag, message=''):
        """Log timing message to stderr.

        Logs message about `request' with a `tag' (a string, 10
        characters or less if possible), timing info and optional
        `message'.

        Log format is "timestamp tag uuid count path +delta message"
        - timestamp is microsecond timestamp of message
        - tag is the `tag' parameter
        - uuid is the UUID identifying request
        - count is number of logged message for this request
        - path is request.path
        - delta is timedelta between first logged message
          for this request and current message
        - message is the `message' parameter.
        """

        dt = datetime.datetime.utcnow()
        if not hasattr(request, '_logging_uuid'):
            request._logging_uuid = uuid.uuid1()
            request._logging_start_dt = dt
            request._logging_pass = 0

        request._logging_pass += 1

        # Replace this with logging output

        logger.info('%s %-10s %s %2d %s +%s %s' % (
                    dt.isoformat(),
                    tag,
                    request._logging_uuid,
                    request._logging_pass,
                    request.path,
                    dt - request._logging_start_dt,
                    message)
                    )

    def process_request(self, request):
        self.log_message(request, 'request ')

    def process_response(self, request, response):
        s = getattr(response, 'status_code', 0)
        r = str(s)
        if s in (300, 301, 302, 307):
            r += ' => %s' % response.get('Location', '?')
        elif response.content:
            r += ' (%db)' % len(response.content)
        self.log_message(request, 'response', r)
        return response
