# -*- coding: utf-8 -*-
from social.backends.oauth import BaseOAuth2
from django.core.urlresolvers import reverse
from django.conf import settings


class MyOAuthOAuth2(BaseOAuth2):
    name                = settings.PROPRIETARY_BACKEND_NAME
    AUTHORIZATION_URL   = settings.MY_AUTHORIZATION_URL  #  'http://127.0.0.1:8000/o/authorize'
    ACCESS_TOKEN_URL    = settings.MY_ACCESS_TOKEN_URL   #'http://127.0.0.1:8000/o/token'
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_id(self, details, response):
        # Extracts the user id from `user_data` response.
        return response.get('id')

    def get_user_details(self, response):
        """
        Return user details from MYOAUTH account
        """
        # At the moment we generate a random user data, for demonstration
        # purposes.
        return {
            'username': response.get('username'),
            'first_name': response.get('username'),
            'last_name': 'Test',
            'email': response.get('email'),
        }

    def user_data(self, access_token, *args, **kwargs):
        """
        Loads user data from service
        """
        # To work properly, we need to set up an api endpoint that returns
        # user profile informations. Something like:
        #
        #   return self.get_json('http://127.0.0.1:8000/api/profile/',
        #                        params={'access_token': access_token})
        #
        # At the moment we just mock the response with random user informations.
        import random
        import string
        username = ''.join(random.choice(string.ascii_letters) for x in range(10))
        email = "%s@test.net" % username
        return {
            'id': random.randint(1, 999999),
            'username': username,
            'first_name': username,
            'last_name': 'Test',
            'email': email,
        }
