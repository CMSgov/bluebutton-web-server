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


def create_group(name="BlueButton"):

    g, created = Group.objects.get_or_create(name=name)
    if created:
        print("%s group created" % (name))
    else:
        print("%s group pre-existing. Create skipped." % (name))
    return g


def get_switch(name):
    try:
        sw = Switch.objects.get(name=name)
        return sw.active
    except Exception as e:
        print(f"Could not get switch {name}: {e}")


def set_switch(name, b):
    # DISABLE SOME WAFFLE SWITCHES
    # We don't want email, etc.
    sw, _ = Switch.objects.get_or_create(name=name)
    sw.active = b
    sw.save()

# usr would be a string if it is anything


def create_user(group, usr):
    u_name = "rogersf"
    first_name = "Fred"
    last_name = "Rogers"
    email = "fred@landofmakebelieve.gov"
    password = "danielthetiger"
    user_type = "BEN"

    if usr is not None:
        u_name = usr
        first_name = "{}{}".format(usr, "First")
        last_name = "{}{}".format(usr, "Last")
        email = "{}.{}@{}".format(first_name, last_name, email)
        user_type = "DEV"

    # This violates constraints on other tables.
    usr_q = User.objects.filter(username=u_name)
    if usr_q.exists():
        # Delete any ADAGs for this user, or we will run into a
        # constraint issue at startup.
        count = ArchivedDataAccessGrant.objects.filter(beneficiary=usr_q.first()).delete()
        print(f"Deleted {count} ADAGs for {u_name}")
        count = DataAccessGrant.objects.filter(beneficiary=usr_q.first()).delete()
        print(f"Deleted {count} ADAGs for {u_name}")

        User.objects.filter(username=u_name).delete()

    u = None

    if usr is not None:
        try:
            u, _ = User.objects.get_or_create(username=u_name,
                                              first_name=first_name,
                                              last_name=last_name,
                                              email=email,
                                              signals_to_disable=["post_save"])
            u.set_unusable_password()
        except Exception as e:
            print(f"Did not create user: {e}")
    else:
        # create a sample user 'fred' for dev local that has a usable password
        try:
            # get_or_create returns a tuple (v, bool)
            u, _ = User.objects.get_or_create(username=u_name,
                                              first_name=first_name,
                                              last_name=last_name,
                                              email=email,
                                              password=password,)

            UserProfile.objects.create(user=u,
                                       user_type=user_type,
                                       create_applications=True,
                                       password_reset_question_1='1',
                                       password_reset_answer_1='blue',
                                       password_reset_question_2='2',
                                       password_reset_answer_2='Frank',
                                       password_reset_question_3='3',
                                       password_reset_answer_3='Bentley')
        except Exception as e:
            print(f"Did not create user and profile: {e}")

    if u is None:
        print(f"Error creating user; exiting.")
    else:
        u.groups.add(group)

    user_id_hash = "ee78989d1d9ba0b98f3cfbd52479f10c7631679c17563186f70fbef038cc9536"
    Crosswalk.objects.filter(_user_id_hash=user_id_hash).delete()
    c, _ = Crosswalk.objects.get_or_create(user=u,
                                           fhir_id_v2=settings.DEFAULT_SAMPLE_FHIR_ID_V2,
                                           _user_id_hash=user_id_hash)
    return u


def create_application(user, group, app, redirect):
    app_name = "TestApp" if app is None else app
    Application.objects.filter(name=app_name).delete()
    redirect_uri = "{}{}".format(settings.HOSTNAME_URL, settings.TESTCLIENT_REDIRECT_URI)

    if redirect:
        redirect_uri = redirect

    if not (redirect_uri.startswith("http://") or redirect_uri.startswith("https://")):
        redirect_uri = "https://" + redirect_uri

    try:
        a = Application.objects.create(name=app_name,
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
            a.scope.add(c)
        return a
    except Exception as e:
        print(f"Skipped creation of {app_name}: {e}")


def create_test_token(user, application):

    now = timezone.now()
    expires = now + timedelta(days=1)

    scopes = application.scope.all()
    scope = []
    for s in scopes:
        scope.append(s.slug)

    t = AccessToken.objects.create(user=user, application=application,
                                   token="sample-token-string",
                                   expires=expires,
                                   scope=' '.join(scope),)

    return t


class Command(BaseCommand):
    help = 'Create a test user and application for the test client'

    def add_arguments(self, parser):
        parser.add_argument("-u", "--user", help="Name of the user to be created (unique).")
        parser.add_argument("-a", "--app", help="Name of the application to be created (unique).")
        parser.add_argument("-r", "--redirect", help="Redirect url of the application.")

    def handle(self, *args, **options):
        usr = options.get("user", None)
        app = options.get("app", None)
        redirect = options["redirect"]

        set_switch('outreach_email', False)

        g = create_group()
        u = create_user(g, usr)
        print(f"Created user {u}")
        a = create_application(u, g, app, redirect)
        t = None
        if usr is None and app is None:
            t = create_test_token(u, a)
            update_grants()
        print("Name:", a.name)
        print("client_id:", a.client_id)
        print("client_secret:", a.client_secret)
        print("access_token:", t.token if t else "None")
        print("redirect_uri:", a.redirect_uris)

        # Restore switch to whatever it was.
        set_switch('outreach_email', True)
