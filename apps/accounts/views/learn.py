"""
bbofuser
FILE: learn
Created: 8/10/15 9:18 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

from django.conf import settings
from django.http import HttpResponse
from django.template import loader


def learn_0(request):
    # Show Education Page 0

    if settings.DEBUG:
        print(settings.APPLICATION_TITLE, "in accounts.views.learn.learn_0")

    context = {}

    template = loader.get_template('accounts/education_0.html')
    return HttpResponse(template.render(context, request))


def learn_1(request):
    # Show Education Page 1

    if settings.DEBUG:
        print(settings.APPLICATION_TITLE, "in accounts.views.learn.learn_1")

    context = {}

    template = loader.get_template('accounts/education_1.html')
    return HttpResponse(template.render(context, request))


def learn_2(request):
    # Show Home Page

    if settings.DEBUG:
        print(settings.APPLICATION_TITLE, "in accounts.views.learn.learn_2")

    context = {}

    template = loader.get_template('accounts/education_2.html')
    return HttpResponse(template.render(context, request))
