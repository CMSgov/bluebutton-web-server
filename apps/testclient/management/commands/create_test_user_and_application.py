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


def create_group(name="BlueButton"):

    g, created = Group.objects.get_or_create(name=name)
    if created:
        print("%s group created" % (name))
    else:
        print("%s group pre-existing. Create skipped." % (name))
    return g


def create_user(group, usr):
    u_name = "fred"
    first_name = "Fred"
    last_name = "Flinstone"
    email = "fred@example.com"
    password = "foobarfoobarfoobar"
    user_type = "BEN"

    if usr is not None:
        u_name = usr
        first_name = "{}{}".format(usr, "First")
        last_name = "{}{}".format(usr, "Last")
        email = "{}.{}@example.com".format(first_name, last_name)
        user_type = "DEV"

    if User.objects.filter(username=u_name).exists():
        User.objects.filter(username=u_name).delete()

    u = None

    if usr is not None:
        u = User.objects.create_user(username=u_name,
                                     first_name=first_name,
                                     last_name=last_name,
                                     email=email)
        u.set_unusable_password()
    else:
        # create a sample user 'fred' for dev local that has a usable password
        u = User.objects.create_user(username=u_name,
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

    u.groups.add(group)

    if usr is None:
        if not Crosswalk.objects.filter(_user_id_hash="ee78989d1d9ba0b98f3cfbd52479f10c7631679c17563186f70fbef038cc9536").exists():
            c, g_o_c = Crosswalk.objects.get_or_create(user=u,
                                                       fhir_id_v2=settings.DEFAULT_SAMPLE_FHIR_ID_V2,
                                                       _user_id_hash="ee78989d1d9ba0b98f3cfbd52479f10c7631679c17563186f70fbef038cc9536")
        else:
            print("Skipping crosswalk creation; already exists.")
    return u


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


def create_test_token(user, application):

    now = timezone.now()
    expires = now + timedelta(days=1)

    scopes = application.scope.all()
    scope = []
    for s in scopes:
        scope.append(s.slug)

    if AccessToken.objects.filter(token="sample-token-string").exists():
        t = AccessToken.objects.get(token="sample-token-string")

        t = AccessToken.objects.create(user=user, application=application,
                                       token="sample-token-string",
                                       expires=expires,
                                       scope=' '.join(scope))
    return t


class Command(BaseCommand):
    help = 'Create a test user and application for the test client'

    def add_arguments(self, parser):
        parser.add_argument("-u", "--user", help="Name of the user to be created (unique).")
        parser.add_argument("-a", "--app", help="Name of the application to be created (unique).")
        parser.add_argument("-r", "--redirect", help="Redirect url of the application.")

    def handle(self, *args, **options):
        usr = options["user"]
        app = options["app"]
        redirect = options["redirect"]

        g = create_group()
        u = create_user(g, usr)
        a = create_application(u)  # a = create_application(u, g, app, redirect)
        t = None
        if usr is None and app is None:
            t = create_test_token(u, a)
            update_grants()
        print("Name:", a.name)
        print("client_id:", a.client_id)
        print("client_secret:", a.client_secret)
        print("access_token:", t.token if t else "None")
        print("redirect_uri:", a.redirect_uris)
