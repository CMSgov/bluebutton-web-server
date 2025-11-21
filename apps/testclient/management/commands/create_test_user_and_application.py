import pytz

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.fhir.bluebutton.models import Crosswalk
from apps.dot_ext.models import Application
from apps.capabilities.models import ProtectedCapability
from oauth2_provider.models import AccessToken
from django.utils import timezone
from datetime import timedelta, datetime
from django.conf import settings
from apps.authorization.models import update_grants
from apps.authorization.models import ArchivedDataAccessGrant, DataAccessGrant

# Imports for quieting things during startup.
from waffle.models import Switch

from uuid import uuid4


def create_group(name="BlueButton"):
    g, created = Group.objects.get_or_create(name=name)
    if created:
        print("%s group created" % (name))
    else:
        print("%s group pre-existing. Create skipped." % (name))
    return g

# usr would be a string if it is anything


def create_user(the_group):
    username = "rogersf"
    first_name = "Fred"
    last_name = "Rogers"
    email = "mrrogers@landofmakebelieve.gov"
    password = uuid4()
    user_type = "BEN"

    # We will do this over-and-over.
    # If we don't already exist, then create the user.
    if User.objects.filter(username=username).exists():
        print(f"👟 {username} already exists. Skipping test user creation.")
        return User.objects.get(username=username)

    # If the user didn't exist, it is our first time through.
    # Create the user.
    user_obj = User.objects.create(username=username,
                                   first_name=first_name,
                                   last_name=last_name,
                                   email=email,
                                   password=password,)
    user_obj.set_unusable_password()
    UserProfile.objects.create(user=user_obj,
                               user_type=user_type,
                               create_applications=True,
                               password_reset_question_1='1',
                               password_reset_answer_1='blue',
                               password_reset_question_2='2',
                               password_reset_answer_2='Frank',
                               password_reset_question_3='3',
                               password_reset_answer_3='Bentley')
    user_obj.groups.add(the_group)

    # CROSSWALK
    # Removing any existing crosswalks for this artificial user.
    # Why? Just in case.
    user_id_hash = "ee78989d1d9ba0b98f3cfbd52479f10c7631679c17563186f70fbef038cc9536"
    Crosswalk.objects.filter(_user_id_hash=user_id_hash).delete()
    Crosswalk.objects.get_or_create(user=user_obj,
                                    fhir_id_v2=settings.DEFAULT_SAMPLE_FHIR_ID_V2,
                                    _user_id_hash=user_id_hash)
    return user_obj


def create_application(user):
    app_name = "TestApp"
    if Application.objects.filter(name=app_name).exists():
        return Application.objects.get(name=app_name)

    # If the app doesn't exist, create the test app.

    Application.objects.filter(name=app_name).delete()
    redirect_uri = "{}{}".format(settings.HOSTNAME_URL, settings.TESTCLIENT_REDIRECT_URI)

    the_app = Application.objects.create(name=app_name,
                                         redirect_uris=redirect_uri,
                                         user=user,
                                         data_access_type="THIRTEEN_MONTH",
                                         client_type="confidential",
                                         authorization_grant_type="authorization-code",)

    titles = ["My Medicare and supplemental coverage information.",
              "My Medicare claim information.",
              "My general patient and demographic information.",
              "Profile information including name and email."
              ]

    for t in titles:
        c = ProtectedCapability.objects.get(title=t)
        the_app.scope.add(c)

    return the_app


def create_test_token(the_user, the_app):

    # Set expiration one day from now.
    now = timezone.now()
    expires = now + timedelta(days=1)

    scopes = the_app.scope.all()
    scope = []
    for s in scopes:
        scope.append(s.slug)

    # We have to have a tokent with token="sample-token-string", because we
    # rely on it existing for unit tests. Which are actually integration tests.
    if AccessToken.objects.filter(token="sample-token-string").exists():
        t = AccessToken.objects.get(token="sample-token-string")
        t.expires = expires
        t.save()
    else:
        AccessToken.objects.create(user=the_user,
                                   application=the_app,
                                   # This needs to be "sample-token-string", because
                                   # we have tests that rely on it.
                                   token="sample-token-string",
                                   expires=expires,
                                   scope=' '.join(scope),)


def get_switch(name):
    try:
        sw = Switch.objects.get(name=name)
        return sw.active
    except Exception as e:
        print(f"Could not get switch {name}: {e}")


def set_switch(name, b):
    sw, _ = Switch.objects.get_or_create(name=name)
    sw.active = b
    sw.save()


class Command(BaseCommand):
    help = 'Create a test user and application for the test client'

    def handle(self, *args, **options):

        set_switch('outreach_email', False)

        the_group = create_group()
        the_user = create_user(the_group)
        the_app = create_application(the_user)
        create_test_token(the_user, the_app)
        update_grants()

        # Restore switch to whatever it was.
        set_switch('outreach_email', True)
