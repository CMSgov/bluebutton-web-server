from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import activate

class LanguageMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = request.session.get('django_language')
        if language:
            activate(language)
        return self.get_response(request)