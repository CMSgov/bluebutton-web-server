from django.core.urlresolvers import reverse

__author__ = "Alan Viars"


def reverse_sin_trailing_slash(s):
    url = reverse(s)
    if url.endswith('/'):
        url = url[:-1]
    return url
