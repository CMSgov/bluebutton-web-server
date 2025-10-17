from django.core.exceptions import ValidationError

# Anywhere we want to use/reference/manipulate versions,
# we should use this class as opposed to interned strings.
# e.g. A use of 'v1' should become Versions.V1.


class Versions:
    V1 = 'v1'
    V2 = 'v2'
    V3 = 'v3'

    # If we use a default version anywhere, this is the current
    # default version for BB2
    DEFAULT_API_VERSION = V2

    # In some cases, we need to default to an API version.
    # For now, we are defaulting to v2.
    NOT_AN_API_VERSION = 'v0'

    def as_int(version: str) -> int:
        match version:
            case Versions.V1:
                return 1
            case Versions.V2:
                return 2
            case Versions.V3:
                return 3
            case _:
                # FIXME MCJ: Raise an exception here.
                # Do something noisy. We should not end up here.
                raise ValidationError(f"{version} is not a valid version constant")
