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
            data = json.loads(protected_resource)
        except (json.JSONDecodeError, TypeError):
            continue  # Skip invalid JSON strings

        # Check if the parsed JSON is empty (e.g., None, {}, or [])
        if not data:
            continue

        # Ensure it's always a list of lists
        rules = data if any(isinstance(i, list) for i in data) else [data]

        for method, path in rules:
            if method.upper() == request.method.upper():
                if path == request.path or re.fullmatch(path, request.path):
                    return True
    return False
