import json
import hashlib
# from oauth2_provider.models import AccessToken


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
