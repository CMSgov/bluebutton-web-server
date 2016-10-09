# from django.test import TestCase
from apps.test import BaseApiTest
from django.contrib.auth.models import User

from apps.accounts.models import UserProfile
from .models import fhir_Consent

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
        logger.debug("\n APP:%s" % app)

        create_consent = fhir_Consent()
        create_consent.user = u
        create_consent.application = app
        create_consent.save()

        logger.debug("\n created Consent:%s" % create_consent)
        logger.debug("\nKey:%s" % create_consent.key)
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
        print("\n APP:%s" % app)

        create_consent = fhir_Consent()
        create_consent.user = u
        create_consent.application = app
        create_consent.save()

        logger.debug("\n created Consent:%s" % create_consent)
        logger.debug("\nKey:%s" % create_consent.key)

        revocation = create_consent.revoke_consent(True)
        logger.debug("\n Revocation:%s" % revocation)
        logger.debug("\nRevoked:%s" % create_consent.revoked.strftime("%Y-%M-%DT%H:%M:%S"))

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
        print("\n APP:%s" % app)

        create_consent = fhir_Consent()
        create_consent.user = u
        create_consent.application = app
        create_consent.save()

        logger.debug("\n created Consent:%s" % create_consent)
        logger.debug("\nKey:%s" % create_consent.key)

        granted = create_consent.status()
        self.assertEqual(granted, "VALID")

        revocation = create_consent.revoke_consent(True)
        logger.debug("\n Revocation:%s" % revocation)
        logger.debug("\nRevoked:%s" % create_consent.revoked.strftime("%Y-%M-%DT%H:%M:%S"))


        expected = "REVOKED"
        result = create_consent.status()
        logger.debug("\nStatus:%s" % result)

        self.assertEqual(result, expected)
