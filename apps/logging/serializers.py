import json
import hashlib
# from oauth2_provider.models import AccessToken


class DataAccessGrantSerializer:
    tkn = None
    action = None

    def __init__(self, obj, action=None):
        self.tkn = obj
        self.action = action

    def __str__(self):
        # seems like this should be a serializer
        result = {
            "type": "DataAccessGrant",
            "action": self.action,
            "id": self.tkn.pk,
            "application": {
                "id": self.tkn.application.id,
                "name": self.tkn.application.name,
                "user": {
                    "id": self.tkn.application.user.id,
                    "username": self.tkn.application.user.username,
                },
            },
            "user": {
                "id": self.tkn.user.id,
                "username": self.tkn.user.username,
            }
        }
        return json.dumps(result)


class Token:
    tkn = None
    action = None

    def __init__(self, obj, action=None):
        self.tkn = obj
        self.action = action

    def __str__(self):
        # seems like this should be a serializer
        result = {
            "type": "AccessToken",
            "action": self.action,
            "id": self.tkn.pk,
            "access_token": hashlib.sha256(
                str(self.tkn.token).encode('utf-8')).hexdigest(),
            "application": {
                "id": self.tkn.application.id,
                "name": self.tkn.application.name,
                "user": {
                    "id": self.tkn.application.user.id,
                    "username": self.tkn.application.user.username,
                },
            },
            "user": {
                "id": self.tkn.user.id,
                "username": self.tkn.user.username,
            }
        }
        return json.dumps(result)


class Request:
    # requests.PrepairedRequest
    req = None

    def __init__(self, request):
        self.req = request

    def get_request(self):
        return self.req

    def to_dict(self):
        result = {
            "uuid": self.uuid(),
            "user": self.user(),
            "start_time": self.start_time(),
            "application": self.application(),
            "path": self.path(),
        }
        return result

    def __str__(self):
        return json.dumps(self.to_dict())


class SLSRequest(Request):

    def uuid(self):
        return self.req.headers.get('X-Request-ID')

    def user(self):
        return None

    def start_time(self):
        return None

    def application(self):
        return None

    def path(self):
        return self.req.path


class FHIRRequest(Request):

    def uuid(self):
        return self.req.headers.get('BlueButton-OriginalQueryId')

    def user(self):
        return self.req.headers.get('BlueButton-BeneficiaryId')

    def start_time(self):
        return self.req.headers.get('BlueButton-OriginalQueryTimestamp')

    def application(self):
        return {
            "name": self.req.headers.get('BlueButton-Application'),
            "id": self.req.headers.get('BlueButton-ApplicationId'),
            "user": {
                "id": self.req.headers.get('BlueButton-DeveloperId'),
            },
        }

    def path(self):
        return self.req.headers.get('BlueButton-OriginalUrl')


class Response:
    request_class = None
    resp = None

    def __init__(self, response):
        self.resp = response
        # http://docs.python-requests.org/en/master/api/#requests.Response.request
        self.req = self.request_class(response.request).to_dict() if response.request else {}

    def code(self):
        return self.resp.status_code

    def size(self):
        return len(self.resp.content)

    def elapsed(self):
        return self.resp.elapsed.total_seconds()

    def to_dict(self):
        return {
            "code": self.code(),
            "size": self.size(),
            "elapsed": self.elapsed(),
        }

    def __str__(self):
        result = self.to_dict().copy()
        result.update(self.req)
        return json.dumps(result)


class FHIRResponse(Response):
    request_class = FHIRRequest


class SLSResponse(Response):
    request_class = SLSRequest
