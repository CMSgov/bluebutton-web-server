from django.views.decorators.cache import never_cache
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.decorators import renderer_classes
from django.contrib.auth.models import User
from ..accounts.models import UserProfile
# from ..fhir.bluebutton.models import Crosswalk


# Metric auth and response
@never_cache
@api_view(['GET'])
@renderer_classes((JSONRenderer,))
def metric_response(request, content):
    if request.user.is_authenticated() and request.user.is_staff:
        return Response(content)
    else:
        return HttpResponse('Unauthorized', status=401)


# User records count
def total_user_count(request, format=None):
        return metric_response(request,
                               {'total_user_count', User.objects.count()})


# User active records count
def active_user_count(request, format=None):
        return metric_response(request,
                               {'active_user_count': User.objects.filter(is_active=True).count()})


# User staff records count
def staff_user_count(request, format=None):
        return metric_response(request,
                               {'staff_user_count': User.objects.filter(is_staff=True).count()})


# User super-user/admin records count
def super_user_count(request, format=None):
        return metric_response(request,
                               {'admin_user_count': User.objects.filter(is_superuser=True).count()})


# UserProfile records count
def total_user_profile_count(request, format=None):
        return metric_response(request,
                               {'total_user_profile_count': UserProfile.objects.count()})


# DEV UserProfile records count
def dev_user_profile_count(request, format=None):
        return metric_response(request,
                               {'dev_user_profile_count': UserProfile.objects.filter(user_type='DEV').count()})


# BEN UserProfile records count
def ben_user_profile_count(request, format=None):
        return metric_response(request,
                               {'ben_user_profile_count': UserProfile.objects.filter(user_type='BEN').count()})
