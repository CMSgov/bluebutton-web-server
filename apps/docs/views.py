from apps.docs.constants import OPENAPI_OAUTH2_REDIRECT_PAGE, OPENAPI_PAGE
from django.http import Http404
from django.shortcuts import render
from waffle import switch_is_active



def openapi(request):
    # serve swagger ui landing page
    if not switch_is_active("enable_swaggerui"):
        raise Http404("enable_swaggerui not active.")
    return render(request, OPENAPI_PAGE)


def openapi_oauth2_redirect(request):
    # serve swagger ui landing page
    if not switch_is_active("enable_swaggerui"):
        raise Http404("enable_swaggerui not active.")
    return render(request, OPENAPI_OAUTH2_REDIRECT_PAGE)
