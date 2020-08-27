import json
import hashlib
import random
from enum import Enum, unique


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
        return {
            "uuid": self.uuid(),
            "user": self.user(),
            "start_time": self.start_time(),
            "application": self.application(),
            "path": self.path(),
        }

    def __str__(self):
        return json.dumps(self.to_dict())


class SLSRequest(Request):

    def uuid(self):
        return self.req.headers.get('X-Request-ID')

    def user(self):
        return 'Unavailable'

    def start_time(self):
        return self.req.headers.get('X-SLS-starttime')

    def application(self):
        return 'Unavailable'

    def path(self):
        return self.req.path_url if self.req.path_url else None


class FHIRRequest(Request):

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
        return {
            "uuid": self.uuid(),
            "fhir_id": self.fhir_id(),
            "user": self.user(),
            "start_time": self.start_time(),
            "application": self.application(),
            "path": self.path(),
        }


class Response:
    request_class = None
    resp = None
    auth_uuid = None

    def __init__(self, response, auth_uuid):
        self.auth_uuid = auth_uuid
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
        resp_dict = {
            "code": self.code(),
            "size": self.size(),
            "elapsed": self.elapsed(),
        }
        resp_dict.update(self.req)
        return resp_dict

    def __str__(self):
        result = self.to_dict().copy()
        result.update(self.req)
        return json.dumps(result)


class FHIRResponse(Response):
    request_class = FHIRRequest


class SLSResponse(Response):
    def to_dict(self):
        resp_dict = super().to_dict().copy()
        resp_dict.update({
            'type': self.get_type(),
            'auth_uuid': self.auth_uuid,
        })
        return resp_dict 


class SLSTokenResponse(SLSResponse):
    request_class = SLSRequest

    def get_type(self):
        return 'SLS_token'

    def to_dict(self):
        event_dict = super().to_dict().copy()
        event_dict.update(json.loads(self.resp.text))
        return {
            "type": event_dict['type'],
            "code": event_dict['code'],
            "size": event_dict['size'],
            "start_time": event_dict['start_time'],
            "elapsed": event_dict['elapsed'],
            "uuid": event_dict['uuid'],
            "auth_uuid": event_dict['auth_uuid'],
            "user": event_dict['user'],
            "application": event_dict['application'],
            "path": event_dict['path'],
            "access_token": hashlib.sha256(
                str(event_dict['access_token']).encode('utf-8')).hexdigest(),
        }

    def __str__(self):
        result = self.to_dict()
        result.update(self.req)
        return json.dumps(result)


class SLSUserInfoResponse(SLSResponse):
    request_class = SLSRequest

    def get_type(self):
        return 'SLS_userinfo'

    def to_dict(self):
        event_dict = super().to_dict().copy()
        event_dict.update(json.loads(self.resp.text))
        return {
            "type": event_dict['type'],
            "code": event_dict['code'],
            "size": event_dict['size'],
            "start_time": event_dict['start_time'],
            "elapsed": event_dict['elapsed'],
            "uuid": event_dict['uuid'],
            "auth_uuid": event_dict['auth_uuid'],
            "user": event_dict['user'],
            "application": event_dict['application'],
            "path": event_dict['path'],
            "sub": event_dict['sub'],
        }

    def __str__(self):
        result = self.to_dict()
        result.update(self.req)
        return json.dumps(result)
