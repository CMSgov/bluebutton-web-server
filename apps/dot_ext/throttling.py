from rest_framework.throttling import SimpleRateThrottle
from django.utils.deprecation import MiddlewareMixin


HEADERS = {
    'Remaining': 'X-RateLimit-Remaining',
    'Limit': 'X-RateLimit-Limit',
    'Reset': 'X-RateLimit-Reset',
}


class TokenRateThrottle(SimpleRateThrottle):
    """
    Limits the rate of API calls that may be made from a given token.
    The token will be used as a unique cache key.
    For anonymous requests, the IP address of the request will
    be used.
    """
    scope = 'token'

    def get_cache_key(self, request, view):
        try:
            ident = request.auth
        except AttributeError:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident,
        }

    def allow_request(self, request, view):
        # run this first to populate/update self.history, self.now, self.duration, self.num_requests
        result = super(TokenRateThrottle, self).allow_request(request, view)
        try:
            request.META[HEADERS['Remaining']] = self.num_requests - len(self.history)
            request.META[HEADERS['Limit']] = self.num_requests
            if self.history:
                remaining_duration = self.duration - (self.now - self.history[-1])
            else:
                remaining_duration = self.duration

            request.META[HEADERS['Reset']] = remaining_duration
        # Allows for throttling to be turned off completely
        except AttributeError:
            pass

        return result


class ThrottleMiddleware(MiddlewareMixin):
    scope = 'throttle'

    def process_response(self, request, response):
        """
        Setting the standard rate limit headers
        :param request:
        :param response:
        :return:
        """
        response[HEADERS['Limit']] = request.META.get(HEADERS['Limit'])
        response[HEADERS['Remaining']] = request.META.get(HEADERS['Remaining'])
        response[HEADERS['Reset']] = request.META.get(HEADERS['Reset'])
        return response
