import json
import base64
import pytz

from django.db import transaction
from django.db.utils import IntegrityError
from django.http import HttpRequest
from django.utils import timezone
from django.urls import reverse

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from urllib.parse import parse_qs, urlparse

from oauth2_provider.models import (
    get_application_model,
    get_access_token_model,
)

from apps.test import BaseApiTest, flag_is_active
from apps.authorization.models import (
    DataAccessGrant,
    ArchivedDataAccessGrant,
    check_grants,
    update_grants,

)
from waffle import get_waffle_flag_model
from waffle.testutils import override_flag, override_switch

Application = get_application_model()
AccessToken = get_access_token_model()


class TestDataAccessGrant(BaseApiTest):

    @staticmethod
    def _create_authorization_header(client_id, client_secret):
        return "Basic {0}".format(
            base64.b64encode("{0}:{1}".format(client_id, client_secret).encode('utf-8')).decode('utf-8'))

    def test_create_update_delete(self):
        # 1. Test create and default expiration_date
        dev_user = self._create_user("developer_test", "123456")
        bene_user = self._create_user("test_beneficiary", "123456")
        test_app = self._create_application("test_app", user=dev_user)

        DataAccessGrant.objects.create(
            application=test_app,
            beneficiary=bene_user,
        )
        dag = DataAccessGrant.objects.get(
            beneficiary__username="test_beneficiary", application__name="test_app"
        )

        #     Is the default Null?
        self.assertEqual(None, dag.expiration_date)

        # 2. Test expire_date updated.
        dag.expiration_date = datetime(2030, 1, 15, 0, 0, 0, 0, pytz.UTC)
        dag.save()
        dag = DataAccessGrant.objects.get(
            beneficiary__username="test_beneficiary", application__name="test_app"
        )
        self.assertEqual("2030-01-15 00:00:00+00:00", str(dag.expiration_date))

        # 3. Test unique constraints.
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                DataAccessGrant.objects.create(
                    application=test_app,
                    beneficiary=bene_user,
                )

        # 4. Test delete and archived.
        #     Verify it doesn't exist yet.
        with self.assertRaises(ArchivedDataAccessGrant.DoesNotExist):
            ArchivedDataAccessGrant.objects.get(
                beneficiary__username="test_beneficiary", application__name="test_app"
            )

        dag = DataAccessGrant.objects.get(
            beneficiary__username="test_beneficiary", application__name="test_app"
        )

        dag.delete()

        #     Verify it does exist and archived.
        arch_dag = ArchivedDataAccessGrant.objects.get(
            beneficiary__username="test_beneficiary", application__name="test_app"
        )

        #    Verify expiration_date copied OK.
        self.assertEqual("2030-01-15 00:00:00+00:00", str(arch_dag.expiration_date))

    @override_flag('limit_data_access', active=False)
    def test_thirteen_month_app_type_without_switch_limit_data_access(self):
        assert not flag_is_active('limit_data_access')

        # 1. Create bene and app for tests
        dev_user = self._create_user("developer_test", "123456")
        bene_user = self._create_user("test_beneficiary", "123456")
        test_app = self._create_application("test_app", user=dev_user,
                                            data_access_type="THIRTEEN_MONTH")

        flag = get_waffle_flag_model().get('limit_data_access')
        assert flag.id is None or flag.is_active_for_user(dev_user) is False

        # 2. Create grant with expiration date in future.
        dag = DataAccessGrant.objects.create(
            application=test_app,
            beneficiary=bene_user
        )

        # 3. Test expiration_date not set
        self.assertEqual(dag.expiration_date, None)
        #    Test has_expired() with None is false
        self.assertEqual(dag.has_expired(), False)

        # 4. Test has_expired() true for -1 hour ago is false w/o switch enabled
        dag.expiration_date = datetime.now().replace(tzinfo=pytz.UTC) + relativedelta(
            hours=-1
        )
        self.assertEqual(dag.has_expired(), False)

        # 5. Test has_expired() false for +1 hour in future.
        dag.expiration_date = datetime.now().replace(tzinfo=pytz.UTC) + relativedelta(
            hours=+1
        )
        self.assertEqual(dag.has_expired(), False)

        # 6. Test has_expired() false for ONE_TIME type
        test_app.data_access_type = "ONE_TIME"
        test_app.save()
        self.assertEqual(dag.has_expired(), False)

        # 7. Test has_expired() false for RESEARCH_STUDY type
        test_app.data_access_type = "RESEARCH_STUDY"
        test_app.end_date = datetime(2030, 1, 15, 0, 0, 0, 0, pytz.UTC)
        test_app.save()
        self.assertEqual(dag.has_expired(), False)

    @override_flag('limit_data_access', active=True)
    def test_thirteen_month_app_type_with_switch_limit_data_access(self):
        assert flag_is_active('limit_data_access')

        # 1. Create bene and app for tests
        dev_user = self._create_user("developer_test", "123456")
        bene_user = self._create_user("test_beneficiary", "123456")
        test_app = self._create_application("test_app", user=dev_user,
                                            data_access_type="THIRTEEN_MONTH")

        flag = get_waffle_flag_model().get('limit_data_access')
        assert flag.id is not None and flag.is_active_for_user(dev_user)

        # 2. Create grant with expiration date in future.
        dag = DataAccessGrant.objects.create(
            application=test_app,
            beneficiary=bene_user
        )

        # 3. Test update expiration_date on instance
        dag.update_expiration_date()
        #    Date is updated OK.
        self.assertNotEqual(dag.expiration_date, None)

        # 4. Test has_expired() true for -1 hour ago
        dag.expiration_date = datetime.now().replace(tzinfo=pytz.UTC) + relativedelta(
            hours=-1
        )
        self.assertEqual(dag.has_expired(), True)

        # 5. Test has_expired() false for +1 hour in future.
        dag.expiration_date = datetime.now().replace(tzinfo=pytz.UTC) + relativedelta(
            hours=+1
        )
        self.assertEqual(dag.has_expired(), False)

        # 6. Test has_expired() false for ONE_TIME type
        test_app.data_access_type = "ONE_TIME"
        test_app.save()
        self.assertEqual(dag.has_expired(), False)

        # 7. Test has_expired() false for RESEARCH_STUDY type
        test_app.data_access_type = "RESEARCH_STUDY"
        test_app.end_date = datetime(2030, 1, 15, 0, 0, 0, 0, pytz.UTC)
        test_app.save()
        self.assertEqual(dag.has_expired(), False)

    def test_creation_on_approval(self):
        user = self._create_user("anna", '123456')
        application, fhir_id = self.setup_test_application_with_user(user)
        # errors if DNE or more than one is found
        DataAccessGrant.objects.get(beneficiary=user.id, application=application.id)

    @override_switch('expire_grant_endpoint', active=True)
    def test_delete_authenticated_user_grant(self):
        # 1. create user, app, ac
        user, application, ac = self._create_user_app_token_grant(
            first_name="first",
            last_name="last1",
            fhir_id="-20140000008325",
            app_name="test_app1",
            app_username="devuser1",
            app_user_organization="org1",
        )

        user, application_2, ac = self._create_user_app_token_grant(
            first_name="first",
            last_name="last1",
            fhir_id="-20140000008325",
            app_name="test_app2",
            app_username="devuser2",
            app_user_organization="org2",
        )

        # 2. verify grant creation - errors if DNE or more than one is found
        DataAccessGrant.objects.get(beneficiary=user.id, application=application.id)
        DataAccessGrant.objects.get(beneficiary=user.id, application=application_2.id)

        # 3. logout
        self.client.logout()

        # 4. call without authentication and expect 403
        response = self.client.post('/v1/o/expire_authenticated_user/{0}/'.format("-20140000008325"))
        self.assertEqual(response.status_code, 403)

        # 5. Create authentication headers and expect success
        auth = self._create_authorization_header(application.client_id, application.client_secret)
        response = self.client.post('/v1/o/expire_authenticated_user/{0}/'.format("-20140000008325"),
                                    HTTP_AUTHORIZATION=auth,
                                    )
        self.assertEqual(response.status_code, 200)

        # 6. verify grant deleted - errors if DNE or more than one is found
        with self.assertRaises(DataAccessGrant.DoesNotExist):
            DataAccessGrant.objects.get(beneficiary=user.id, application=application.id)

        # 7. verify archived grant exists - errors if DNE or more than one is found
        ArchivedDataAccessGrant.objects.get(beneficiary=user.id, application=application.id)

        # 8. verify second grant still exists - errors if DNE or more than one is found
        DataAccessGrant.objects.get(beneficiary=user.id, application=application_2.id)

        # 9 test should error if patient id isn't found
        response = self.client.post('/v1/o/expire_authenticated_user/{0}/'.format("-20140000008325XXX"),
                                    HTTP_AUTHORIZATION=auth,
                                    )
        self.assertEqual(response.status_code, 404)

    def setup_test_application_with_user(self, test_user, application_name='an app'):
        redirect_uri = 'http://localhost'
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            application_name,
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            user=test_user,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username=test_user.username, password='123456')
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
        }
        response = self.client.get('/v1/o/authorize', data=payload)
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(response['Location'], data=payload)
        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
        }
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        fhir_id = json.loads(response.content)["patient"]
        self.assertEqual(response.status_code, 200)
        return application, fhir_id

    def test_no_action_on_reapproval(self):
        redirect_uri = 'http://localhost'

        user = self._create_user("anna", '123456')
        application, fhir_id = self.setup_test_application_with_user(user)

        # errors if DNE or more than one is found
        DataAccessGrant.objects.get(beneficiary=user.id, application=application.id)

        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
        }
        response = self.client.get('/v1/o/authorize', data=payload)
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }
        response = self.client.post(response['Location'], data=payload)

        self.assertEqual(response.status_code, 302)
        # now extract the authorization code and use it to request an access_token
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
        }
        response = self.client.post(reverse('oauth2_provider:token'), data=token_request_data)
        self.assertEqual(response.status_code, 200)

        # errors if DNE or more than one is found
        DataAccessGrant.objects.get(beneficiary=user.id, application=application.id)

    def test_check_and_update_grants(self):
        redirect_uri = 'http://localhost'
        # create a user
        user = self._create_user('anna', '123456')
        user2 = self._create_user('bob', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)

        AccessToken.objects.create(
            token="existingtoken",
            user=user,
            application=application,
            expires=timezone.now() + timedelta(seconds=10),
        )

        checks = check_grants()
        self.assertGreater(
            checks['unique_tokens'],
            checks['grants'],
        )

        update_grants()

        checks = check_grants()
        self.assertEqual(
            checks['unique_tokens'],
            checks['grants'],
        )

        # create expired token
        AccessToken.objects.create(
            token="expiredtoken",
            user=user2,
            application=application,
            expires=timezone.now() - timedelta(seconds=10),
        )

        checks = check_grants()
        self.assertEqual(
            checks['unique_tokens'],
            checks['grants'],
        )

        update_grants()

        checks = check_grants()
        self.assertEqual(
            checks['unique_tokens'],
            checks['grants'],
        )

    def test_permission_deny_on_app_or_org_disabled(self):
        '''
        BB2-149 leverage application.active, user.is_active to deny permission
        to an application or applications under a user (organization)
        '''
        redirect_uri = 'http://localhost'
        # create a user
        user = self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            user=user,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a)
        application.active = False
        application.save()
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')

        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
        }
        response = self.client.get('/v1/o/authorize', data=payload)
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
        }

        response = self.client.post(response['Location'], data=payload)
        self.assertEqual(response.status_code, 401)
        # pretty good evidence for in active app permission denied
        self.assertEqual(response.template_name, "app_inactive_401.html")
        # set back app and user to active - not to affect other tests
        application.active = True
        application.save()

    def test_thirteen_month_app_needs_limit_data_access_set(self):

        # 1. Create benes
        dev_user = self._create_user("developer_test", "123456")
        bene_user = self._create_user("test_beneficiary", "123456")
        flag_bene_user = self._create_user("flag_beneficiary", "123456")
        test_app = self._create_application("test_app", user=dev_user,
                                            data_access_type="THIRTEEN_MONTH")

        # 2. Create flag and show is not set for dev_user
        flag = get_waffle_flag_model().objects.create(name='limit_data_access')
        assert flag.id is not None
        assert not flag.is_active_for_user(dev_user)

        # 3. Create grant and expire expiration to show it doesn't matter
        dag = DataAccessGrant.objects.create(
            application=test_app,
            beneficiary=bene_user
        )
        # 4. Test has_expired() true for -1 hour ago
        dag.expiration_date = datetime.now().replace(tzinfo=pytz.UTC) + relativedelta(
            hours=-1
        )
        self.assertEqual(dag.has_expired(), False)

        # 4. Add dev_user to flag
        flag.users.add(dev_user)

        # 5. Create new grant and show expiration is working
        flag_dag = DataAccessGrant.objects.create(
            application=test_app,
            beneficiary=flag_bene_user
        )
        flag_dag.expiration_date = datetime.now().replace(tzinfo=pytz.UTC) + relativedelta(
            hours=-1
        )
        self.assertEqual(dag.has_expired(), True)
