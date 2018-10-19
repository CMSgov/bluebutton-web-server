from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_resourcerouter
from apps.dot_ext.models import Application
from apps.capabilities.models import ProtectedCapability
from oauth2_provider.models import AccessToken
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import random
import string


def create_group(name="BlueButton"):

    g, created = Group.objects.get_or_create(name=name)
    if created:
        print("%s group created" % (name))
    else:
        print("%s group pre-existing. Create skipped." % (name))
    return g


def create_user(group):
    uname = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    password = "foobarfoobarfoobar"

    if User.objects.filter(username=uname).exists():
        User.objects.filter(username=uname).delete()

    u = User.objects.create_user(username=uname,
                                 first_name="Fred",
                                 last_name="Flinstone",
                                 email="{}@example.com".format(uname),
                                 password=password,)
    UserProfile.objects.create(user=u,
                               user_type="BEN",
                               create_applications=True,
                               password_reset_question_1='1',
                               password_reset_answer_1='blue',
                               password_reset_question_2='2',
                               password_reset_answer_2='Frank',
                               password_reset_question_3='3',
                               password_reset_answer_3='Bentley')

    u.groups.add(group)
    c, g_o_c = Crosswalk.objects.get_or_create(user=u,
                                               fhir_id=settings.DEFAULT_SAMPLE_FHIR_ID,
                                               fhir_source=get_resourcerouter())
    return u


def create_application(user, group):
    appname = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    redirect_uri = "%s/testclient/callback" % (settings.HOSTNAME_URL)
    if not(redirect_uri.startswith("http://") or redirect_uri.startswith("https://")):
        redirect_uri = "https://" + redirect_uri
    a = Application.objects.create(name=appname,
                                   redirect_uris=redirect_uri,
                                   user=user,
                                   client_type="confidential",
                                   authorization_grant_type="authorization-code")

    return a


def create_test_token(user, application):

    now = timezone.now()
    expires = now + timedelta(days=1)

    scopes = application.scope.all()
    scope = []
    for s in scopes:
        scope.append(s.slug)

    tkn = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    t = AccessToken.objects.create(user=user, application=application,
                                   token=tkn,
                                   expires=expires,
                                   scope=' '.join(scope))
    return t


class Command(BaseCommand):
    help = 'Create many test users and applications'

    def handle(self, *args, **options):
        numusers = 500
        num_apps_per_user = 4
        g = create_group()
        for i in range(numusers):
            u = create_user(g)
            for j in range(num_apps_per_user):
                a = create_application(u, g)
                t = create_test_token(u, a)
