import io
import json
import logging

from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.test import TestCase
from django.utils.text import slugify
from django.conf import settings

from apps.fhir.bluebutton.models import Crosswalk
from apps.authorization.models import DataAccessGrant
from apps.capabilities.models import ProtectedCapability
from apps.dot_ext.models import Application


class BaseApiTest(TestCase):
    """
    This class contains some helper methods useful to test API endpoints
    protected with oauth2 using DOT.
    """

    test_hicn_hash = "96228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7"
    test_mbi_hash = "98765432137efea543f4f370f96f1dbf01c3e3129041dba3ea43675987654321"

    def _create_user(self, username, password,
                     fhir_id=settings.DEFAULT_SAMPLE_FHIR_ID,
                     user_hicn_hash=test_hicn_hash,
                     user_mbi_hash=test_mbi_hash,
                     **extra_fields):
        """
        Helper method that creates a user instance
        with `username` and `password` set.
        """
        user = User.objects.create_user(username, password=password, **extra_fields)
        if Crosswalk.objects.filter(_fhir_id=fhir_id).exists():
            Crosswalk.objects.filter(_fhir_id=fhir_id).delete()

        cw, _ = Crosswalk.objects.get_or_create(user=user,
                                                _fhir_id=fhir_id,
                                                _user_id_hash=user_hicn_hash,
                                                _user_mbi_hash=user_mbi_hash)
        cw.save()
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
        dev_user = user or User.objects.create_user('dev', password='123456')
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
        DataAccessGrant.objects.update_or_create(
            beneficiary=User.objects.get(username=username),
            application=application)
        # Unpack the response and return the token string
        content = json.loads(response.content.decode("utf-8"))
        return content['access_token']

    def _get_user_application(self, username, app_name):
        """
        Helper method that retrieve application with given user and app name.
        """
        apps_qs = Application.objects.filter(name__exact=app_name).filter(user__username=username)
        return apps_qs.first()

    def create_token(self, first_name, last_name):
        passwd = '123456'
        user = self._create_user(first_name,
                                 passwd,
                                 first_name=first_name,
                                 last_name=last_name,
                                 email="%s@%s.net" % (first_name, last_name))
        if Crosswalk.objects.filter(_fhir_id=settings.DEFAULT_SAMPLE_FHIR_ID).exists():
            Crosswalk.objects.filter(_fhir_id=settings.DEFAULT_SAMPLE_FHIR_ID).delete()
        Crosswalk.objects.create(user=user,
                                 fhir_id=settings.DEFAULT_SAMPLE_FHIR_ID,
                                 user_hicn_hash=self.test_hicn_hash,
                                 user_mbi_hash=self.test_mbi_hash)

        # create a oauth2 application and add capabilities
        application = self._create_application("%s_%s_test" % (first_name, last_name), user=user)
        application.scope.add(self.read_capability, self.write_capability)
        # get the first access token for the user 'john'
        return self._get_access_token(first_name,
                                      passwd,
                                      application)

    def _redirect_loggers(self, logger_names):
        self.logger_registry = {}
        for n in logger_names:
            logger = logging.getLogger(n)
            log_buffer = io.StringIO()
            log_channel = logging.StreamHandler(log_buffer)
            log_channel.setLevel(logging.INFO)
            logger.setLevel(logging.INFO)
            logger.addHandler(log_channel)
            self.logger_registry[n] = (log_buffer, log_channel)

    def _cleanup_logger(self):
        # do not close stream, only close channel
        for k, v in self.logger_registry.items():
            v[1].close()
        self.logger_registry.clear()

    def _collect_logs(self, logger_names):
        log_contents = {}
        for n in logger_names:
            v = self.logger_registry.get(n)
            log_contents[n] = v[0].getvalue()
        return log_contents

    def assert_log_entry_valid(self, entry_dict, compare_dict, attrexist_list, hasvalue_list):
        '''
        Method for validating a log entry has the expected structure and values
        '''
        # Make a copy to work with so that the original is not modified
        copy_dict = entry_dict.copy()

        # Check that all items are included and there are no additional items
        expected_keys = []
        entry_keys = []

        for key in compare_dict:
            expected_keys.append(key)

        for item in attrexist_list:
            expected_keys.append(item)

        for key in entry_dict:
            entry_keys.append(key)

        self.assertEqual(expected_keys.sort(), entry_keys.sort())

        # Remove items not needed for comparison and check that they have values (not None/empty)
        for key in attrexist_list:
            self.assertTrue(key in copy_dict)
            if hasvalue_list is not None and key in hasvalue_list:
                self.assertIsNotNone(copy_dict[key])
                self.assertNotEqual(copy_dict[key], '')
            copy_dict.pop(key)

        # Compare dictionaries for expected values
        self.assertDictEqual(copy_dict, compare_dict)
