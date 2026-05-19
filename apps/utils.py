import json
import re

from rest_framework.request import Request


def is_valid_scope(scopes: list[str], request: Request) -> bool:
    """
    Determines if the scope is valid.

    args:
      - scopes: The scopes retreived from the database
      - request: The API request
    returns:
      - True if there is a match with the current request and the scope it has in the database, False if not
    """
    for scope in scopes:
        data = json.loads(scope)
        if isinstance(data, list) and len(data) == 0:
            continue
        for method, path in data:
            if method != request.method:
                continue
            if path == request.path:
                return True
            if re.fullmatch(path, request.path) is not None:
                return True
    return False
