from django.core.cache import cache
from oauth2_provider.models import AccessToken
import requests
import threading

BEARER_STRING_LENGTH = 7


class InjectApplicationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # try:
        #     print("request.app_id check: ", request.application_id)
        # except AttributeError as e:
        #     print("app_id was not already set")
        #     print(e)
        #     request.application_id = self._get_application_id(request)
        #     print("but now it is: ", request.application_id)
        request.application_id = self._get_application_id(request)
        response = self.get_response(request)
        return response

    def _get_application_id(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        # print("AUTH_HEADER: ", auth_header)
        if not auth_header.startswith("Bearer "):
            # print("we are returning here unfortunately: ", request.__dict__)
            return None

        token_string = auth_header[BEARER_STRING_LENGTH:]
        cache_key = f"token_app_id:{token_string}"

        # Check cache first
        cached = cache.get(cache_key)
        if cached is not None:
            print("CACHE RETURN")
            return None if cached == "__none__" else cached

        # Nothing in cache — query the DB
        try:
            token = AccessToken.objects.get(
                token=token_string
            )
            app_id = token.application.id
        except AccessToken.DoesNotExist:
            # Cache the miss to avoid repeated lookups
            app_id = "__none__"

        print("WHAT IS THE APP_ID: ", app_id)
        # Cache for 5 minutes
        cache.set(cache_key, app_id, timeout=300)
        return None if app_id == "__none__" else app_id


class ITSLogAPIMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if 'testclient' in request.path:
            # Don't want testclient events being posted to ITS-log
            return response
        threading.Thread(target=self._ping_api, args=(request,), daemon=True).start()
        return response

    def _ping_api(self, request):
        try:
            # print('about to post')
            requests.post(
                "http://host.docker.internal:8888/v1/log",
                headers={"x-api-key": "12345678901234561234567890123456"},
                # headers={"x-api-key", "1234567890123456123456789012345612345678901234561234567890123456"},
                json={
                    # "source": "my-django-app",
                    "tags": self._build_tags(request),
                    "value": f"{request.path}",
                    "type": "text"
                },
                timeout=2
            )
        except Exception as e:
            print("ERROR FROM ITS-LOG middleware 1217: ", e)
            pass  # Never let logging failures crash your app

    def _build_tags(self, request):
        tags = []

        path_parts = [p for p in request.path.strip("/").split("/") if p and p != 'fhir']
        tags.extend(path_parts)

        app_id = getattr(request, "application_id", None)
        if app_id:
            # print("APPLICATION_ID: ", request.application_id)
            tags.append(str(app_id))
        # print('tags - ', tags)
        return tags
