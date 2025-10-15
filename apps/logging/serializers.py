import json
import hashlib


class DataAccessGrantSerializer:
    tkn = None
    action = None

    def __init__(self, obj, action=None):
        self.tkn = obj
        self.action = action

    def to_dict(self):
        # seems like this should be a serializer
        app = getattr(self.tkn, 'application', None)
        app_user = getattr(app, 'user', None)
        user = getattr(self.tkn, 'user', None)
        return {
            "type": "DataAccessGrant",
            "action": self.action,
            "id": getattr(self.tkn, 'pk', None),
            "application": {
                "id": getattr(app, 'id', None),
                "name": getattr(app, 'name', None),
                "data_access_type": getattr(app, 'data_access_type', None),
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


class Token:
    tkn = None
    action = None

    def __init__(self, obj, action=None):
        self.tkn = obj
        self.action = action

    def to_dict(self):
        # seems like this should be a serializer
        app = getattr(self.tkn, 'application', None)
        app_user = getattr(app, 'user', None)
        user = getattr(self.tkn, 'user', None)
        scopes_dict = getattr(self.tkn, 'scopes', None)
        crosswalk = getattr(user, 'crosswalk', None)

        if scopes_dict:
            # Convert dict keys list to str
            scopes = " ".join(scopes_dict.keys())
        else:
            scopes = ""

        result = {
            "type": "AccessToken",
            "action": self.action,
            "id": getattr(self.tkn, 'pk', None),
            "access_token": hashlib.sha256(
                str(getattr(self.tkn, 'token', None)).encode('utf-8')).hexdigest(),
            "scopes": scopes,
            "application": {
                "id": getattr(app, 'id', None),
                "name": getattr(app, 'name', None),
                "data_access_type": getattr(app, 'data_access_type', None),
                "user": {
                    "id": getattr(app_user, 'id', None),
                    "username": getattr(app_user, 'username', None),
                },
            },
            "user": {
                "id": getattr(user, 'id', None),
                "username": getattr(user, 'username', None),
            },
            "crosswalk": {
                "id": getattr(crosswalk, 'id', None),
                "user_hicn_hash": getattr(crosswalk, "user_hicn_hash", None),
                "user_mbi_hash": getattr(crosswalk, "user_mbi_hash", None),
                "fhir_id": getattr(crosswalk, "fhir_id", None),
                "user_id_type": getattr(crosswalk, "user_id_type", None),
            },
        }

        return result


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


class SLSRequest(Request):

    def uuid(self):
        return self.req.headers.get('X-Request-ID')

    def user(self):
        pass

    def start_time(self):
        return self.req.headers.get('X-SLS-starttime')

    def application(self):
        pass

    def path(self):
        return self.req.path_url if self.req.path_url else None


class FHIRRequest(Request):
    def __init__(self, request, api_ver=None):
        self.api_ver = api_ver
        super().__init__(request)

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
        return {
            "type": "fhir_pre_fetch",
            "uuid": self.uuid(),
            "fhir_id": self.fhir_id(),
            "api_ver": self.api_ver if self.api_ver is not None else 'v1',
            "includeAddressFields": self.includeAddressFields(),
            "user": self.user(),
            "application": self.application(),
            "path": self.path(),
            "start_time": self.start_time(),
        }


class FHIRRequestForAuth(Request):
    def __init__(self, request, api_ver=None):
        self.api_ver = api_ver
        super().__init__(request)

    def includeAddressFields(self):
        return self.req.headers.get('includeAddressFields')

    def uuid(self):
        return self.req.headers.get('BlueButton-OriginalQueryId')

    def start_time(self):
        return self.req.headers.get('BlueButton-OriginalQueryTimestamp')

    def to_dict(self):
        result = {
            "type": "fhir_auth_pre_fetch",
            "uuid": self.uuid(),
            "api_ver": self.api_ver if self.api_ver is not None else 'v1',
            "includeAddressFields": self.includeAddressFields(),
            "path": "patient search",
            "start_time": self.start_time(),
        }
        return result


class Response:
    request_class = None

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
        resp_dict.update(self.req)
        return resp_dict


class FHIRResponse(Response):
    request_class = FHIRRequest

    def __init__(self, response, api_ver):
        self.api_ver = api_ver
        super().__init__(response)

    def to_dict(self):
        super_dict = super().to_dict()
        # add fhir version info
        super_dict.update({"api_ver": self.api_ver if self.api_ver is not None else 'v1'})
        # over write type
        super_dict.update({"type": "fhir_post_fetch"})
        return super_dict


class FHIRResponseForAuth(Response):
    request_class = FHIRRequestForAuth

    def __init__(self, response, api_ver=None):
        self.api_ver = api_ver
        super().__init__(response)

    def to_dict(self):
        super_dict = super().to_dict()
        # add fhir version info
        super_dict.update({"api_ver": self.api_ver if self.api_ver is not None else 'v1'})
        # over write type
        super_dict.update({"type": "fhir_auth_post_fetch"})
        return super_dict


class SLSResponse(Response):

    def __init__(self, response, request=None):
        super().__init__(response)

    def to_dict(self):
        resp_dict = super().to_dict().copy()
        resp_dict.update({
            'type': self.get_type(),
        })
        return resp_dict


class SLSxTokenResponse(SLSResponse):
    request_class = SLSRequest

    def get_type(self):
        return 'SLSx_token'

    def to_dict(self):

        event_dict = {}
        json_exception = {}

        if self.resp.text:
            try:
                event_dict = json.loads(self.resp.text)
            except json.decoder.JSONDecodeError:
                json_exception = {
                    "message": f"JSONDecodeError thrown when parsing response text. See response text.",
                    # 20251015 FIXME/WARNING MCJ: Can we add this to the logs safely?
                    "response_text": self.resp.text,
                }

        event_dict.update(super().to_dict().copy())

        resp_dict = {
            "type": event_dict.get('type', 'unknown'),
            "uuid": event_dict.get('uuid', ''),
            "path": event_dict.get('path', ''),
            "auth_token": 'Not available' if event_dict.get('auth_token') is None else hashlib.sha256(
                str(event_dict.get('auth_token')).encode('utf-8')).hexdigest(),
            "code": event_dict.get('code', 306),
            "size": event_dict.get('size', 0),
            "start_time": event_dict.get('start_time', ''),
            "elapsed": event_dict.get('elapsed', 0.0),
        }

        # update json parse err if any
        resp_dict.update(json_exception)

        return resp_dict


class SLSxUserInfoResponse(SLSResponse):
    request_class = SLSRequest

    def get_type(self):
        return 'SLSx_userinfo'

    def to_dict(self):
        # handle case where response text is empty or none json,
        # e.g. reconcile with additional slsx flow singout validation
        # added to slsx flow

        event_dict = {}
        json_exception = {}

        if self.resp.text:
            try:
                event_dict = json.loads(self.resp.text)
            except json.decoder.JSONDecodeError:
                json_exception = {
                    "message": "JSONDecodeError thrown when parsing response text."
                }

        event_dict.update(super().to_dict().copy())

        resp_dict = {
            "type": event_dict.get('type', ''),
            "uuid": event_dict.get('uuid', ''),
            "path": event_dict.get('path', ''),
            "sub": event_dict.get('data', {}).get('user', {}).get('id', 'Not available'),
            # use http unused code as place holder - unittests now check schema
            "code": event_dict.get('code', 306),
            "size": event_dict.get('size', 0),
            "start_time": event_dict.get('start_time', ''),
            "elapsed": event_dict.get('elapsed', 0.0),
        }

        # update json parse err if any
        resp_dict.update(json_exception)

        return resp_dict
