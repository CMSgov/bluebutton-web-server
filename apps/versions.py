# Anywhere we want to use/reference/manipulate versions,
# we should use this class as opposed to interned strings.
# e.g. A use of 'v1' should become Versions.V1.

def noisy_has_permission(original_class):
    orig_has_perm = original_class.has_permission

    def has_permission(self, request, view):
        class_obj = self.__class__
        class_name = class_obj.__name__
        print(f" --> has_permission: {class_name} <--")
        return orig_has_perm(self, request, view)

    original_class.has_permission = has_permission
    return original_class


class VersionNotMatched(Exception):
    """
    A custom exception to be thrown when we do not match a version.
    """
    pass


class Versions:
    V1 = 1
    V2 = 2
    V3 = 3

    # If we use a default version anywhere, this is the current
    # default version for BB2
    DEFAULT_API_VERSION = V2

    # In some cases, we need to default to an API version.
    # For now, we are defaulting to v2.
    NOT_AN_API_VERSION = 0

    @staticmethod
    def as_str(version: int):
        return f'v{version}'

    @staticmethod
    def as_int(version: int) -> int:
        match version:
            case Versions.V1:
                return 1
            case Versions.V2:
                return 2
            case Versions.V3:
                return 3
            case _:
                raise VersionNotMatched(f"{version} is not a valid version constant")

    @staticmethod
    def supported_versions():
        return [Versions.V1, Versions.V2, Versions.V3]

    @staticmethod
    def latest_versions():
        return [Versions.V2, Versions.V3]


class AccessType:
    ONE_TIME = 'ONE_TIME'
    RESEARCH_STUDY = 'RESEARCH_STUDY'
    THIRTEEN_MONTH = 'THIRTEEN_MONTH'
