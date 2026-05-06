

class AuthorizationViewMiddleware:
    AUTHORIZATION_PATH = '/o/authorize/'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self.AUTHORIZATION_PATH in request.path:
            # Read from session and attach directly to the request object
            request.beneficiary_name = request.session.get('beneficiary_name', None)

        response = self.get_response(request)
        return response
