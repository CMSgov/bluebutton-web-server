# import io
import json
import re

from django.contrib.auth.models import User, Group
from django.http import HttpRequest
from django.urls import reverse
from django.test import TestCase
from django.utils.text import slugify
from django.conf import settings
from urllib.parse import parse_qs, urlparse


from apps.accounts.models import UserProfile
from apps.authorization.models import DataAccessGrant
from apps.capabilities.models import ProtectedCapability
from apps.dot_ext.models import Application, InternalApplicationLabels
from apps.dot_ext.utils import (
    remove_application_user_pair_tokens_data_access,
)
from apps.fhir.bluebutton.models import Crosswalk
from waffle import get_waffle_flag_model


def flag_is_active(name):
    flag = get_waffle_flag_model().get(name)
    return flag.everyone


class BaseApiTest(TestCase):
    """
    This class contains some helper methods useful to test API endpoints
    protected with oauth2 using DOT.
    """

    test_hicn_hash = "96228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7"
    test_mbi_hash = "98765432137efea543f4f370f96f1dbf01c3e3129041dba3ea43675987654321"
    test_mbi = "1SA0A00AA00"

    def _create_user(
        self,
        username,
        password,
        fhir_id_v2=settings.DEFAULT_SAMPLE_FHIR_ID_V2,
        fhir_id_v3=settings.DEFAULT_SAMPLE_FHIR_ID_V3,
        user_hicn_hash=test_hicn_hash,
        user_mbi_hash=test_mbi_hash,
        user_type=None,
        **extra_fields
    ):
        """
        Helper method that creates a user instance
        with `username` and `password` set.
        """
        user = User.objects.create_user(username, password=password, **extra_fields)
        if Crosswalk.objects.filter(fhir_id_v2=fhir_id_v2).exists():
            Crosswalk.objects.filter(fhir_id_v2=fhir_id_v2).delete()

        cw, _ = Crosswalk.objects.get_or_create(
            user=user,
            _user_id_hash=user_hicn_hash,
            _user_mbi_hash=user_mbi_hash,
        )
        cw.set_fhir_id(fhir_id_v2, 2)
        cw.save()
        # Create ben user profile, if it doesn't exist
        if user_type:
            try:
                UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(user=user,
                                           user_type="BEN",
                                           create_applications=False)
        return user

    def _create_group(self, name):
        """
        Helper method that creates a group instance
        with `name`.
        """
        group, _ = Group.objects.get_or_create(name=name)
        return group

    def _create_application(
        self,
        name,
        client_type=None,
        grant_type=None,
        capability=None,
        user=None,
        data_access_type=None,
        **kwargs
    ):
        """
        Helper method that creates an application instance
        with `name`, `client_type` and `grant_type` and `capability`.

        The default client_type is 'public'.
        The default grant_type is 'password'.
        """
        client_type = client_type or Application.CLIENT_PUBLIC
        grant_type = grant_type or Application.GRANT_PASSWORD
        # This is the user to whom the application is bound.
        dev_user = user or User.objects.create_user("dev", password="123456")
        application = Application.objects.create(
            name=name,
            user=dev_user,
            client_type=client_type,
            authorization_grant_type=grant_type,
            **kwargs
        )

        label = self._create_internal_application_labels(
            label="Research app - multiple studies",
            slug="research-app-multiple-studies",
            description="Desc: place holder")

        application.internal_application_labels.add(label)

        if data_access_type:
            application.data_access_type = data_access_type

        if data_access_type:
            application.save()

        # add capability
        if capability:
            application.scope.add(capability)
        return application

    def _create_capability(self, name, urls, group=None, default=True):
        """
        Helper method that creates a ProtectedCapability instance
        that controls the access for the set of `urls`.
        """
        # Create capability, if does not already exist
        try:
            capability = ProtectedCapability.objects.get(title=name)
            return capability
        except ProtectedCapability.DoesNotExist:
            pass

        group = group or self._create_group("test")
        capability = ProtectedCapability.objects.create(
            default=default,
            title=name,
            slug=slugify(name),
            protected_resources=json.dumps(urls),
            group=group,
        )
        return capability

    def _create_internal_application_labels(self, label, slug, description):
        """
        Helper method that creates a InternalApplicationLabels instance
        """
        # Create capability, if does not already exist
        try:
            label = InternalApplicationLabels.objects.get(slug=slug)
            return label
        except InternalApplicationLabels.DoesNotExist:
            pass

        label = InternalApplicationLabels.objects.create(
            label=label,
            slug=slug,
            description=description,
        )
        return label

    def _get_access_token(self, username, password, application=None, **extra_fields):
        """
        Helper method that creates an access_token using the password grant.
        """
        # Create an application that supports password grant.
        application = application or self._create_application("test")
        data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": application.client_id,
        }
        data.update(extra_fields)
        # Request the access token
        response = self.client.post(reverse("oauth2_provider:token"), data=data)
        self.assertEqual(response.status_code, 200)
        DataAccessGrant.objects.update_or_create(
            beneficiary=User.objects.get(username=username), application=application
        )
        # Unpack the response and return the token string
        content = json.loads(response.content.decode("utf-8"))
        return content["access_token"]

    def _get_user_application(self, username, app_name):
        """
        Helper method that retrieve application with given user and app name.
        """
        apps_qs = Application.objects.filter(name__exact=app_name).filter(
            user__username=username
        )
        return apps_qs.first()

    def create_token(
        self, first_name, last_name, fhir_id_v2=None, fhir_id_v3=None, hicn_hash=None, mbi_hash=None
    ):
        passwd = "123456"
        user = self._create_user(
            first_name,
            passwd,
            first_name=first_name,
            last_name=last_name,
            fhir_id_v2=fhir_id_v2 if fhir_id_v2 is not None else settings.DEFAULT_SAMPLE_FHIR_ID_V2,
            fhir_id_v3=fhir_id_v3 if fhir_id_v3 is not None else settings.DEFAULT_SAMPLE_FHIR_ID_V3,
            user_hicn_hash=hicn_hash if hicn_hash is not None else self.test_hicn_hash,
            user_mbi_hash=mbi_hash if mbi_hash is not None else self.test_mbi_hash,
            email="%s@%s.net" % (first_name, last_name),
        )
        pt_id = fhir_id_v2 if fhir_id_v2 is not None else settings.DEFAULT_SAMPLE_FHIR_ID_V2

        if Crosswalk.objects.filter(fhir_id_v2=pt_id).exists():
            Crosswalk.objects.filter(fhir_id_v2=pt_id).delete()

        Crosswalk.objects.create(
            user=user,
            fhir_id_v2=pt_id,
            user_hicn_hash=hicn_hash if hicn_hash is not None else self.test_hicn_hash,
            user_mbi_hash=mbi_hash if mbi_hash is not None else self.test_mbi_hash,
        )

        # create a oauth2 application and add capabilities
        application = self._create_application(
            "%s_%s_test" % (first_name, last_name), user=user
        )
        application.scope.add(self.read_capability, self.write_capability)
        # get the first access token for the user 'john'
        return self._get_access_token(first_name, passwd, application)

    def assert_log_entry_valid(
        self, entry_dict, compare_dict, attrexist_list, hasvalue_list
    ):
        """
        Method for validating a log entry has the expected structure and values
        """
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
                self.assertNotEqual(copy_dict[key], "")
            copy_dict.pop(key)

        # Compare dictionaries for expected values
        self.assertDictEqual(copy_dict, compare_dict)

    def _get_access_token_authcode_confidential(
        self, username, user_passwd, application
    ):
        """
        Helper method that creates an access_token using the confidential client and auth_code grant.
        """
        # Dev user logs in
        request = HttpRequest()
        self.client.login(request=request, username=username, password=user_passwd)

        # Authorize
        code_challenge = "sZrievZsrYqxdnu2NVD603EiYBM18CuzZpwB-pOSZjo"
        payload = {
            "client_id": application.client_id,
            "response_type": "code",
            "redirect_uri": application.redirect_uris,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        response = self.client.get("/v1/o/authorize", data=payload)

        # post the authorization form with only one scope selected
        payload = {
            "client_id": application.client_id,
            "response_type": "code",
            "redirect_uri": application.redirect_uris,
            "scope": ["capability-a"],
            "expires_in": 86400,
            "allow": True,
            "state": "0123456789abcdef",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        response = self.client.post(response["Location"], data=payload)
        self.assertEqual(response.status_code, 302)

        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response["Location"]).query)
        authorization_code = query_dict.pop("code")
        token_request_data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": application.redirect_uris,
            "client_id": application.client_id,
            "client_secret": application.client_secret_plain,
        }

        # Test that request is successful WITH the client_secret and GOOD code_verifier
        token_request_data.update(
            {"code_verifier": "test123456789123456789123456789123456789123456789"}
        )
        response = self.client.post(
            reverse("oauth2_provider:token"), data=token_request_data
        )
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content.decode("utf-8"))

        return content

    def _create_or_update_development_user(self, username, organization):
        # Create dev user, if it doesn't exist
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username, password="xxx123")

        # Create dev user profile, if it doesn't exist
        try:
            user_profile = UserProfile.objects.get(user=user)
            user_profile.organization_name = organization
            user_profile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=user,
                                       user_type="DEV",
                                       organization_name=organization,
                                       create_applications=True)
        return user

    def _create_user_app_token_grant(
        self, first_name, last_name, fhir_id, app_name, app_username, app_user_organization,
        app_data_access_type=None
    ):
        """
        Helper method that creates a user connected to an application
        with Crosswalk, Access Token, and Grant for use in tests.
        """
        # Create application dev user
        app_user = self._create_or_update_development_user(app_username, app_user_organization)

        # Create application, if it does not exist.
        try:
            application = Application.objects.get(name=app_name)
        except Application.DoesNotExist:
            application = self._create_application(
                app_name,
                client_type=Application.CLIENT_CONFIDENTIAL,
                grant_type=Application.GRANT_AUTHORIZATION_CODE,
                redirect_uris="com.custom.bluebutton://example.it",
                user=app_user,
                active=True
            )

            # Set data access type
            if app_data_access_type:
                application.data_access_type = app_data_access_type

            # Add a few capabilities
            capability_a = self._create_capability("Capability A", [])
            capability_b = self._create_capability("Capability B", [])
            application.scope.add(capability_a, capability_b)
            application.save()

        # Create beneficiary user, if it doesn't exist
        try:
            username = first_name + last_name + "@example.com"

            # Create unique hashes using FHIR_ID
            hicn_hash = re.sub(
                "[^A-Za-z0-9]+", "a", fhir_id + self.test_hicn_hash[len(fhir_id):]
            )
            mbi_hash = re.sub(
                "[^A-Za-z0-9]+", "a", fhir_id + self.test_mbi_hash[len(fhir_id):]
            )

            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = self._create_user(
                username=username,
                password="xxx123",
                fhir_id_v2=fhir_id,
                user_hicn_hash=hicn_hash,
                user_mbi_hash=mbi_hash,
            )
            # Create bene user profile, if it doesn't exist
            UserProfile.objects.create(user=user,
                                       user_type="BEN",
                                       create_applications=False)

        access_token = self._get_access_token_authcode_confidential(
            username=username, user_passwd="xxx123", application=application
        )

        return user, application, access_token

    def _create_range_users_app_token_grant(self, start_fhir_id, count, app_name,
                                            app_user_organization):
        """
        Helper method that creates a RANGE of users connected to an application
        with Crosswalk, Access Token, and Grant for use in tests.

        Returns a DICT of users granted by fhir_id.
        """
        user_dict = {}
        for i in range(0, count):
            fhir_id_v2 = start_fhir_id + str(i)
            user, app, ac = self._create_user_app_token_grant(
                first_name="first",
                last_name="last" + fhir_id_v2,
                fhir_id=fhir_id_v2,
                app_name=app_name,
                app_username="user_" + app_name,
                app_user_organization=app_user_organization,
            )

            user_dict[fhir_id_v2] = user
        return app, user_dict

    def _revoke_range_users_app_token_grant(self, start_fhir_id, count, app_name):
        """
        Helper method that revokes a RANGE of users (by fhir_id_v2) connected to an application.
        This removes Access Token, and Grant. Useful for testing archived tokens and grants.
        """
        for i in range(0, count):
            fhir_id = start_fhir_id + str(i)
            cw = Crosswalk.objects.get(fhir_id_v2=fhir_id)
            app = Application.objects.get(name=app_name)
            remove_application_user_pair_tokens_data_access(app, cw.user)
