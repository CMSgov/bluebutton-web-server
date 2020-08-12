import json
import hashlib
import random
from enum import Enum, unique


def mask_value(value):
    mask_str = '*' * random.randrange(5, 20)
    return mask_str if value is not None else ''


def hash_value(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


@unique
class SLSEventType(Enum):
    SLS_TOKEN = 'SLS_token'
    SLS_USERINFO = 'SLS_userinfo'


@unique
class SLSEventSender(Enum):
    SLS_TOKEN_EP = 'token_endpoint'
    SLS_USERINFO_EP = 'userinfo_endpoint'


@unique
class SLSToken(Enum):
    TYPE = 'type'
    CODE = 'code'
    SIZE = 'size'
    START_TIME = 'start_time'
    ELAPSED = 'elapsed'
    UUID = 'uuid'
    USER = 'user'
    APPLICATION = 'application'
    PATH = 'path'
    ACCESS_TOKEN = 'access_token'


@unique
class SLSUserInfo(Enum):
    TYPE = 'type'
    CODE = 'code'
    SIZE = 'size'
    START_TIME = 'start_time'
    ELAPSED = 'elapsed'
    UUID = 'uuid'
    USER = 'user'
    APPLICATION = 'application'
    PATH = 'path'
    SUB = 'sub'
    NAME = 'name'
    GIVEN_NAME = 'given_name'
    FAMILY_NAME = 'family_name'
    EMAIL = 'email'
    HICN = 'hicn'
    MBI = 'mbi'


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
        result = {
            "uuid": self.uuid(),
            "fhir_id": self.fhir_id(),
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
        resp_dict = {
            "code": self.code(),
            "size": self.size(),
            "elapsed": self.elapsed(),
        }
        return resp_dict

    def __str__(self):
        result = self.to_dict().copy()
        result.update(self.req)
        return json.dumps(result)


class FHIRResponse(Response):
    request_class = FHIRRequest


class SLSResponse(Response):
    def get_type(self):
        pass

    def get_obfuscation_mapper(self):
        pass

    def extract_and_obfuscate(self, event):
        result = {'type': self.get_type()}
        event_schema = self.get_event_schema()
        obfuscation_mapper = self.get_obfuscation_mapper()
        if event is not None:
            for e in event_schema:
                if e.value in event:
                    attr = event[e.value]
                    if e in obfuscation_mapper:
                        f = obfuscation_mapper[e]
                        attr = f(attr)
                    result[e.value] = attr
        return result


class SLSTokenResponse(SLSResponse):
    obfuscation_mapper = {
        SLSToken.ACCESS_TOKEN: hash_value,
    }

    request_class = SLSRequest

    def get_type(self):
        return SLSEventType.SLS_TOKEN.value

    def get_event_schema(self):
        return SLSToken

    def get_obfuscation_mapper(self):
        return SLSTokenResponse.obfuscation_mapper

    def to_dict(self):
        event_dict = super().to_dict().copy()
        event_dict.update(json.loads(self.resp.text))
        return event_dict

    def __str__(self):
        result = self.to_dict()
        result.update(self.req)
        return json.dumps(self.extract_and_obfuscate(result))


class SLSUserInfoResponse(SLSResponse):
    obfuscation_mapper = {
        SLSUserInfo.NAME: mask_value,
        SLSUserInfo.GIVEN_NAME: mask_value,
        SLSUserInfo.FAMILY_NAME: mask_value,
        SLSUserInfo.EMAIL: mask_value,
        SLSUserInfo.HICN: mask_value,
        SLSUserInfo.MBI: mask_value,
    }

    request_class = SLSRequest

    def get_type(self):
        return SLSEventType.SLS_USERINFO.value

    def get_event_schema(self):
        return SLSUserInfo

    def get_obfuscation_mapper(self):
        return SLSUserInfoResponse.obfuscation_mapper

    def to_dict(self):
        event_dict = super().to_dict().copy()
        event_dict.update(json.loads(self.resp.text))
        return event_dict

    def __str__(self):
        result = self.to_dict()
        result.update(self.req)
        return json.dumps(self.extract_and_obfuscate(result))
