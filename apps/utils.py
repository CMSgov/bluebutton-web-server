import json
import re

from rest_framework.request import Request


def has_matching_protected_resource(protected_resources: list[str], request: Request) -> bool:
    """
    Determines if the protected resource from the request and the app has a match.

    args:
      - protected_resources: The protected resources retreived from the database
      - request: The API request
    returns:
      - True if there is a match with the current request and the protected resource it has in the database, False if not
    """
    for protected_resource in protected_resources:
        try:
            protected_resource_json = json.loads(protected_resource)
        except (json.JSONDecodeError, TypeError):
            continue

        if not protected_resource_json:
            continue

        # Ensure it's always a list of lists
        protected_resource_json_list = (
            protected_resource_json
            if any(isinstance(resource, list) for resource in protected_resource_json)
            else [protected_resource_json]
        )

        for method, path in protected_resource_json_list:
            if method.upper() == request.method.upper():
                if path == request.path or re.fullmatch(path, request.path):
                    return True
    return False
