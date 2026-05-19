import json
import re

from rest_framework.request import Request


def has_matching_protected_resource(protected_resources: list[str], request: Request) -> bool:
    """
    Determines if the protected resource from the request and the app has a match.

    args:
      - scopes: The protected resources retreived from the database
      - request: The API request
    returns:
      - True if there is a match with the current request and the protected resource it has in the database, False if not
    """
    for protected_resource in protected_resources:
        data = json.loads(protected_resource)
        if isinstance(data, list):
            # Move on if it's an empty list
            if len(data) == 0:
                continue
            # Check for list of lists case
            elif isinstance(data[0], list):
                for method, path in data:
                    if method != request.method:
                        continue
                    if path == request.path:
                        return True
                    if re.fullmatch(path, request.path) is not None:
                        return True
            else:
                # Only one list that is a protected resource
                method = data[0]
                path = data[1]
                if method != request.method:
                    continue
                if path == request.path:
                    return True
                if re.fullmatch(path, request.path) is not None:
                    return True
    return False
