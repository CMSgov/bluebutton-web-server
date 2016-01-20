import binascii
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.contrib.auth import authenticate
from django.core.urlresolvers import get_callable
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render_to_response
from django.template import RequestContext
from models import UserProfile


class HTTPAuthBackend(object):
    
    supports_object_permissions=False
    supports_anonymous_user=False
    
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        if user.check_password(password):
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
    
    
class HTTPAuthBackendWithAccessTokens(object):
    
    supports_object_permissions=False
    supports_anonymous_user=False
    
    def authenticate(self, username=None, password=None):
        
        try:
            up = UserProfile.objects.get(access_key_id=username)
            username = up.user.username
        except UserProfile.DoesNotExist:
            return None
        
        if up.access_key_secret == password:
            return up.user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None



