# -*- coding: utf-8 -*-
from social_core.backends.oauth import BaseOAuth2
from django.conf import settings

__author__ = "Alan Viars"


class OAuth2ioOAuth2(BaseOAuth2):
    name = getattr(settings, 'PROPRIETARY_BACKEND_NAME', "oauth2io")
    OAUTH2IO_HOST = getattr(
        settings,
        'OAUTH2IO_HOST',
        "https://dev.bluebutton.cms.fhirservice.net")
    # OAUTH2IO_HOST = getattr(settings, 'OAUTH2IO_HOST', "http://oauth2:8000")
    ID_KEY = 'email'
    AUTHORIZATION_URL = OAUTH2IO_HOST + '/o/authorize/'
    ACCESS_TOKEN_URL = OAUTH2IO_HOST + '/o/token/'
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_profile_url(self):
        """
        Return the url to the user profile endpoint.
        """
        user_profile_url = getattr(
            settings,
            'OAUTH2IO_HOST',
            "https://dev.bluebutton.cms.fhirservice.net") + '/connect/userinfo'
        return user_profile_url

    def get_user_id(self, details, response):
        # Extracts the user id from `user_data` response.
        return response.get('email')

    def get_user_details(self, response):
        """
        Return user details from OAUTH2.IO account
        """
        return {
            'username': response.get('sub'),
            'first_name': response.get('given_name'),
            'last_name': response.get('family_name'),
            'email': response.get('email'),
            'patient': response.get('patient'),
        }

    def user_data(self, access_token, *args, **kwargs):
        """
        Loads user data from service
        """
        return self.get_json(
            self.get_user_profile_url(), params={
                'access_token': access_token})
