from django.shortcuts import render

OPENAPI_PAGE = "openapi.html"


def openapi(request):
    # serve swagger ui landing page
    return render(request, OPENAPI_PAGE)
