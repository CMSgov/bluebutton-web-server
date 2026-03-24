import requests
import threading


class ITSLogAPIMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Fire the ping in a background thread so it doesn't slow down your response
        threading.Thread(target=self._ping_api, args=(request,), daemon=True).start()

        response = self.get_response(request)
        return response

    def _ping_api(self, request):
        try:
            requests.post(
                "http://host.docker.internal:8888/v1/log",
                headers={"x-api-key": "12345678901234561234567890123456"},
                json={
                    "source": "my-django-app",
                    "tags": self._build_tags(request),
                    "value": f"{request.path}",
                    "type": "text"
                },
                timeout=2
            )
        except Exception as e:
            print("ERROR: ", e)
            pass  # Never let logging failures crash your app

    def _build_tags(self, request):
        tags = []

        path_parts = [p for p in request.path.strip("/").split("/") if p and p != 'fhir']
        tags.extend(path_parts)

        return tags
