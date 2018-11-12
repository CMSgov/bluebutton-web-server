import json

from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.test import TestCase
from django.utils.text import slugify
from django.conf import settings

from apps.fhir.bluebutton.utils import get_resourcerouter
from apps.fhir.bluebutton.models import Crosswalk
from apps.capabilities.models import ProtectedCapability
from apps.dot_ext.models import Application


class BaseApiTest(TestCase):
    """
    This class contains some helper methods useful to test API endpoints
    protected with oauth2 using DOT.
    """

    def _create_user(self, username, password, **extra_fields):
        """
        Helper method that creates a user instance
        with `username` and `password` set.
        """
        user = User.objects.create_user(username, password=password, **extra_fields)
        return user

    def _create_group(self, name):
        """
        Helper method that creates a group instance
        with `name`.
        """
        group, _ = Group.objects.get_or_create(name=name)
        return group

    def _create_application(self, name, client_type=None, grant_type=None,
                            capability=None, user=None, **kwargs):
        """
        Helper method that creates an application instance
        with `name`, `client_type` and `grant_type` and `capability`.

        The default client_type is 'public'.
        The default grant_type is 'password'.
        """
        client_type = client_type or Application.CLIENT_PUBLIC
        grant_type = grant_type or Application.GRANT_PASSWORD
        # This is the user to whom the application is bound.
        dev_user = user or self._create_user('dev', '123456')
        application = Application.objects.create(
            name=name, user=dev_user, client_type=client_type,
            authorization_grant_type=grant_type, **kwargs)
        # add capability
        if capability:
            application.scope.add(capability)
        return application

    def _create_capability(self, name, urls, group=None, default=True):
        """
        Helper method that creates a ProtectedCapability instance
        that controls the access for the set of `urls`.
        """
        group = group or self._create_group('test')
        capability = ProtectedCapability.objects.create(
            default=default,
            title=name,
            slug=slugify(name),
            protected_resources=json.dumps(urls),
            group=group)
        return capability

    def _get_access_token(self, username, password, application=None, **extra_fields):
        """
        Helper method that creates an access_token using the password grant.
        """
        # Create an application that supports password grant.
        application = application or self._create_application('test')
        data = {
            'grant_type': 'password',
            'username': username,
            'password': password,
            'client_id': application.client_id,
        }
        data.update(extra_fields)
        # Request the access token
        response = self.client.post(reverse('oauth2_provider:token'), data=data)
        self.assertEqual(response.status_code, 200)
        # Unpack the response and return the token string
        content = json.loads(response.content.decode("utf-8"))
        return content['access_token']

    def create_token(self, first_name, last_name):
        passwd = '123456'
        user = self._create_user(first_name,
                                 passwd,
                                 first_name=first_name,
                                 last_name=last_name,
                                 email="%s@%s.net" % (first_name, last_name))
        Crosswalk.objects.get_or_create(user=user,
                                        fhir_id=settings.DEFAULT_SAMPLE_FHIR_ID,
                                        fhir_source=get_resourcerouter())

        # create a oauth2 application and add capabilities
        application = self._create_application("%s_%s_test" % (first_name, last_name), user=user)
        application.scope.add(self.read_capability, self.write_capability)
        # get the first access token for the user 'john'
        return self._get_access_token(first_name,
                                      passwd,
                                      application,
                                      scope='read')

    def create_token_no_fhir(self, first_name, last_name):
        passwd = '123456'
        user = self._create_user(first_name,
                                 passwd,
                                 first_name=first_name,
                                 last_name=last_name,
                                 email="%s@%s.net" % (first_name, last_name))
        Crosswalk.objects.get_or_create(user=user,
                                        fhir_source=get_resourcerouter())

        # create a oauth2 application and add capabilities
        application = self._create_application("%s_%s_test" % (first_name, last_name), user=user)
        application.scope.add(self.read_capability, self.write_capability)
        # get the first access token for the user 'john'
        return self._get_access_token(first_name,
                                      passwd,
                                      application,
                                      scope='read')
