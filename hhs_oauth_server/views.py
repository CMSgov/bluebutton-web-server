from django.shortcuts import render


def testobject(request):
    # serve akamai test object
    return render(request, "testobject.html")
