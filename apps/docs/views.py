from django.shortcuts import render
from rest_framework import exceptions
from waffle import switch_is_active

OPENAPI_PAGE = "openapi.html"


def openapi(request):
    # serve swagger ui landing page
    if not switch_is_active("enable_swaggerui"):
        # response NOT FOUND 
        raise exceptions.NotFound("enable_swaggerui not active.")
    return render(request, OPENAPI_PAGE)
