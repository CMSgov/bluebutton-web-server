from apps.docs.constants import OPENAPI_OAUTH2_REDIRECT_PAGE, OPENAPI_PAGE
from django.shortcuts import render
from rest_framework import exceptions
from waffle import switch_is_active



def openapi(request):
    # serve swagger ui landing page
    if not switch_is_active("enable_swaggerui"):
        # response NOT FOUND 
        raise exceptions.NotFound("enable_swaggerui not active.")
    return render(request, OPENAPI_PAGE)


def openapi_oauth2_redirect(request):
    # serve swagger ui landing page
    if not switch_is_active("enable_swaggerui"):
        # response NOT FOUND 
        raise exceptions.NotFound("enable_swaggerui not active.")
    return render(request, OPENAPI_OAUTH2_REDIRECT_PAGE)
