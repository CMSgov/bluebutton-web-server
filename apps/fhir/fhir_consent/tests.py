from __future__ import absolute_import
from __future__ import unicode_literals

# from datetime import datetime
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.test import RequestFactory
from apps.test import BaseApiTest
from django.contrib.auth.models import User

from apps.accounts.models import UserProfile
from .models import fhir_Consent
from .views import (rt_consent_activate,
                    rt_consent_directive_activate)
# from ..build_fhir.utils.utils import pretty_json
from ..build_fhir.utils.utils_fhir_dt import dt_period

from ..bluebutton.models import Crosswalk
from .utils import (strip_code_from_scopes)

from oauth2_provider.models import AccessToken

import logging
logger = logging.getLogger('hhs_server.%s' % __name__)


class FHIR_ConsentResourceActionTest(BaseApiTest):
    """ Create a Consent Record """

    def test_createConsentCheckNotRevoked(self):
        """ Check for revoked """

        u = User.objects.create_user(username="billybob",
                                     first_name="Billybob",
                                     last_name="Button",
                                     email='billybob@example.com',
                                     password="foobar",)
        UserProfile.objects.create(user=u,
                                   user_type="DEV",
                                   create_applications=True)

        app = self._create_application('ThePHR', user=u)
        # logger.debug("\n APP:%s" % app)

        create_consent = fhir_Consent()
        create_consent.user = u
        create_consent.application = app
        create_consent.save()

        # logger.debug("\n created Consent:%s" % create_consent)
        # logger.debug("\nKey:%s" % create_consent.key)
        expected = True
        result = create_consent.granted()

        self.assertEqual(result, expected)

    def test_createConsentCheckRevoked(self):
        """ Check for revoked """

        u = User.objects.create_user(username="billybob",
                                     first_name="Billybob",
                                     last_name="Button",
                                     email='billybob@example.com',
                                     password="foobar", )
        UserProfile.objects.create(user=u,
                                   user_type="DEV",
                                   create_applications=True)

        app = self._create_application('ThePHR', user=u)
        # print("\n APP:%s" % app)

        create_consent = fhir_Consent()
        create_consent.user = u
        create_consent.application = app
        create_consent.save()

        # logger.debug("\n created Consent:%s" % create_consent)
        # logger.debug("\nKey:%s" % create_consent.key)

        revocation = create_consent.revoke_consent(True)
        logger.debug("\n Revocation:%s" % revocation)
        # logger.debug("\nRevoked:%s" % create_consent.revoked.strftime("%Y-%M-%DT%H:%M:%S"))

        expected = False
        result = create_consent.granted()

        self.assertEqual(result, expected)

    def test_createConsentCheckStatus(self):
        """ Check for Status """

        u = User.objects.create_user(username="billybob",
                                     first_name="Billybob",
                                     last_name="Button",
                                     email='billybob@example.com',
                                     password="foobar", )
        UserProfile.objects.create(user=u,
                                   user_type="DEV",
                                   create_applications=True)

        app = self._create_application('ThePHR', user=u)
        # print("\n APP:%s" % app)

        create_consent = fhir_Consent()
        create_consent.user = u
        create_consent.application = app
        create_consent.save()

        # logger.debug("\n created Consent:%s" % create_consent)
        # logger.debug("\nKey:%s" % create_consent.key)

        granted = create_consent.status()
        self.assertEqual(granted, "VALID")

        revocation = create_consent.revoke_consent(True)
        logger.debug("\n Revocation:%s" % revocation)
        # logger.debug("\nRevoked:%s" % create_consent.revoked.strftime("%Y-%M-%DT%H:%M:%S"))

        expected = "REVOKED"
        result = create_consent.status()
        # logger.debug("\nStatus:%s" % result)

        self.assertEqual(result, expected)


class FHIR_Consent_Resource_InitializeTest(BaseApiTest):
    """ Test for Consent Initialized """

    def setUp(self):
        # Setup the RequestFactory
        # I could probably update this to use a Mock()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='fred4', email='fred4@...', password='top_secret')

        xwalk = Crosswalk()
        xwalk.user = self.user
        xwalk.fhir_id = "Patient/12345"
        xwalk.save()

    def test_create_Consent(self):
        """ check for a consent record """

        request = self.factory.get('/bluebutton/fhir/v1/ExplanationOfBenefit/')
        request.user = self.user

        app = self._create_application('ThePHR', user=request.user)
        # print("\nApp:%s" % app.name)

        this_moment = timezone.now()
        future_time = this_moment + relativedelta(years=1)
        oauth_period = dt_period(this_moment, future_time)

        oauth_permissions = [{"code": "patient/Patient.read"},
                             {"code": "patient/ExplanationOfBenefit.read"},
                             {"code": "patient/Consent.*"}]

        result = rt_consent_activate(request.user,
                                     app.name,
                                     oauth_period,
                                     oauth_permissions)
        # logger.debug("\nResource:\n%s" % pretty_json(result))

        if 'resourceType' in result:
            result_content = result['resourceType']
            self.assertEqual(result_content, "Consent")


class FHIR_ConsentDirective_Resource_InitializeTest(BaseApiTest):
    """ Test for Consent Initialized """

    def setUp(self):
        # Setup the RequestFactory
        # I could probably update this to use a Mock()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='fred4', email='fred4@...', password='top_secret')

        xwalk = Crosswalk()
        xwalk.user = self.user
        xwalk.fhir_id = "Patient/12345"
        xwalk.save()

    def test_create_ConsentDirective(self):
        """ check for a ConsentDirective record """

        request = self.factory.get('/bluebutton/fhir/v1/ExplanationOfBenefit/')
        request.user = self.user

        xwalk = Crosswalk.objects.get(user=self.user)
        app = self._create_application('ThePHR', user=request.user)
        # print("\nApp:%s" % app.name)

        this_moment = timezone.now()
        future_time = this_moment + relativedelta(years=1)
        oauth_period = dt_period(this_moment, future_time)

        oauth_permissions = [{"code": "patient/Patient.read"},
                             {"code": "patient/ExplanationOfBenefit.read"},
                             {"code": "patient/Consent.*"}]

        oauth_resources = strip_code_from_scopes(oauth_permissions)

        narrative = "<div><h4>Consent Granted</h4>" \
                    "%s grants registered application (%s) " \
                    "access to %s resource data from %s until %s" \
                    "</div>" % (xwalk.fhir_id,
                                app.name,
                                oauth_resources,
                                this_moment.strftime("%Y-%M-%D"),
                                future_time.strftime("%Y-%M-%D"))

        result = rt_consent_directive_activate(request.user,
                                               app.name,
                                               narrative,
                                               oauth_period,
                                               oauth_permissions)
        # logger.debug("\nConsentDirective Resource:\n%s" % pretty_json(result))

        if 'resourceType' in result:
            result_content = result['resourceType']
            self.assertEqual(result_content, "ConsentDirective")


class AccessTokenSignalTest(BaseApiTest):
    """ Testing for signal on AccessToken creation """

    def setUp(self):
        # Setup the RequestFactory
        # I could probably update this to use a Mock()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='fred4', email='fred4@...', password='top_secret')

        xwalk = Crosswalk()
        xwalk.user = self.user
        xwalk.fhir_id = "Patient/12345"
        xwalk.save()

    def test_accesstoken_create(self):
        """ Create an AccessToken and check for signal """

        request = self.factory.get('/bluebutton/fhir/v1/ExplanationOfBenefit/')
        request.user = self.user

        # xwalk = Crosswalk.objects.get(user=self.user)
        app = self._create_application('ThePHR', user=request.user)
        # print("\nApp - prep for AccessToken:%s" % app.name)

        this_moment = timezone.now()
        future_time = this_moment + relativedelta(years=1)

        a_tkn = AccessToken()
        a_tkn.user = request.user
        a_tkn.application = app
        a_tkn.token = "1234567890"
        a_tkn.expires = future_time
        a_tkn.scope = ["patient/Patient.read",
                       "patient/ExplanationOfBenefit.read"]
        a_tkn.save()

        # print("\n================\nSaved %s" % a_tkn)
        self.assertEqual(True, True)

    def test_access_token_signal_update(self):
        """  Create AccessToken check for update to user/app consent """

        usr = self.user
        app = self._create_application('ThePHR', user=usr)
        # xwalk = Crosswalk.objects.get(user=usr)

        this_moment = timezone.now()
        future_time = this_moment + relativedelta(years=1)

        a_tkn = AccessToken()
        a_tkn.user = usr
        a_tkn.application = app
        a_tkn.token = "1234567890"
        a_tkn.expires = future_time
        a_tkn.scope = ["patient/Patient.read",
                       "patient/ExplanationOfBenefit.read"]
        a_tkn.save()

        f_c = fhir_Consent.objects.get(user=usr, application=app)
        # print("\nConsent:%s" % f_c)
        # print("\nJSON Consent:\n%s\n" % pretty_json(f_c.consent))

        self.assertEqual(f_c.consent['meta']['versionId'], "1")

        a_tkn.delete()
        a_tkn = AccessToken()
        a_tkn.user = usr
        a_tkn.application = app
        a_tkn.token = "1234567890"
        a_tkn.expires = future_time
        a_tkn.scope = ["patient/Patient.read",
                       "patient/ExplanationOfBenefit.read"]
        a_tkn.save()

        f_c = fhir_Consent.objects.get(user=usr, application=app)
        # print("\nUpdated Consent:%s" % f_c)
        # print("\nUpdated JSON Consent:\n%s\n" % pretty_json(f_c.consent))

        self.assertEqual(f_c.consent['meta']['versionId'], "2")
