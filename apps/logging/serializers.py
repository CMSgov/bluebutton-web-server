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

    def __init__(self, obj, action=None):
        self.tkn = obj
        self.action = action

    def __str__(self):
        # seems like this should be a serializer
        app = getattr(self.tkn, 'application', None)
        app_user = getattr(app, 'user', None)
        user = getattr(self.tkn, 'user', None)
        result = {
            "type": "AccessToken",
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
        return self.req.path_url if self.req.path_url else None


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
    sender = None

    def __init__(self, response, sender):
        self.resp = response
        self.sender = sender
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
        resp_dict = None
        if self.sender == 'token_endpoint':
            resp_dict = {'type': 'SLS_token'}
            resp_dict.update(json.loads(self.resp.text))
        elif self.sender == 'userinfo_endpoint':
            # mask out mbi and hicn
            resp_dict = {'type': 'SLS_userinfo'}
            d = json.loads(self.resp.text)
            pii_list = ['mbi', 'hicn', 'name', 'given_name', 'family_name', 'email']
            for i in pii_list:
                if i in d:
                    d[i] = '************'
                else:
                    d[i] = None
            resp_dict.update(d)
        else:
            resp_dict.update({'error': 'Unexpected sender: {}'.format(self.sender)})
        result = self.to_dict().copy()
        result.update(self.req)
        result.update(resp_dict)
        return json.dumps(result)


class FHIRResponse(Response):
    request_class = FHIRRequest


class SLSResponse(Response):
    request_class = SLSRequest
