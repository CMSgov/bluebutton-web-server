import json
import hashlib


class DataAccessGrantSerializer:
    tkn = None
    action = None

    def __init__(self, obj, action=None):
        self.tkn = obj
        self.action = action

    def __str__(self):
        # seems like this should be a serializer
        app = getattr(self.tkn, 'application', None)
        app_user = getattr(app, 'user', None)
        user = getattr(self.tkn, 'user', None)
        result = {
            "type": "DataAccessGrant",
            "action": self.action,
            "id": getattr(self.tkn, 'pk', None),
            "application": {
                "id": getattr(app, 'id', None),
                "name": getattr(app, 'name', None),
                "user": {
                    "id": getattr(app_user, 'id', None),
                    "username": getattr(app_user, 'username', None),
                },
            },
            "user": {
                "id": getattr(user, 'id', None),
                "username": getattr(user, 'username', None),
            }
        }
        return json.dumps(result)


class Token:
    tkn = None
    action = None
    auth_uuid = None

    def __init__(self, obj, action=None, auth_uuid=None):
        self.tkn = obj
        self.action = action
        self.auth_uuid = auth_uuid

    def __str__(self):
        # seems like this should be a serializer
        app = getattr(self.tkn, 'application', None)
        app_user = getattr(app, 'user', None)
        user = getattr(self.tkn, 'user', None)
        result = {
            "type": "AccessToken",
            "auth_uuid": self.auth_uuid,
            "action": self.action,
            "id": getattr(self.tkn, 'pk', None),
            "access_token": hashlib.sha256(
                str(getattr(self.tkn, 'token', None)).encode('utf-8')).hexdigest(),
            "application": {
                "id": getattr(app, 'id', None),
                "name": getattr(app, 'name', None),
                "user": {
                    "id": getattr(app_user, 'id', None),
                    "username": getattr(app_user, 'username', None),
                },
            },
            "user": {
                "id": getattr(user, 'id', None),
                "username": getattr(user, 'username', None),
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

    def includeAddressFields(self):
        return self.req.headers.get('includeAddressFields')

    def uuid(self):
        return self.req.headers.get('BlueButton-OriginalQueryId')

    def fhir_id(self):
        # BB2-135 add event field 'fhir_id' per requirement of BFD Insights
        fhir_id = self.req.headers.get('BlueButton-BeneficiaryId', '')
        if fhir_id is not None and fhir_id.startswith('patientId:'):
            fhir_id = fhir_id.split(':')[1]
        return fhir_id

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

    def to_dict(self):
        result = {
            "uuid": self.uuid(),
            "fhir_id": self.fhir_id(),
            "includeAddressFields": self.includeAddressFields(),
            "user": self.user(),
            "start_time": self.start_time(),
            "application": self.application(),
            "path": self.path(),
        }
        return result


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
