from __future__ import absolute_import
from __future__ import unicode_literals
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.fhir.bluebutton.models import Crosswalk
from apps.dot_ext.models import Application
from apps.capabilities.models import ProtectedCapability
from oauth2_provider.models import AccessToken
from django.utils import timezone
from datetime import timedelta


__author__ = "Alan Viars"


def create_group(name="BlueButton"):

    g, created = Group.objects.get_or_create(name=name)
    if created:
        print("%s group created" % (name))
    else:
        print("%s group pre-existing. Create skipped." % (name))
    return g


def create_user(group):

    if User.objects.filter(username="fred").exists():
        User.objects.filter(username="fred").delete()

    u = User.objects.create_user(username="fred",
                                 first_name="Fred",
                                 last_name="Flinstone",
                                 email='fred@example.com',
                                 password="foobarfoobarfoobar",)
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
    c, g_o_c = Crosswalk.objects.get_or_create(user=u, fhir_id="3979")
    return u


def create_application(user, group):
    Application.objects.filter(name="TestApp").delete()

    a = Application.objects.create(name="TestApp",
                                   redirect_uris="http://localhost:8000/testclient/callback",
                                   user=user,
                                   client_type="confidential",
                                   authorization_grant_type="authorization-code")

    titles = ["My Medicare and supplemental coverage information.",
              "My Medicare claim information.",
              "My general patient and demographic information.",
              "Profile information including name and email."
              ]

    for t in titles:
        c = ProtectedCapability.objects.get(title=t)
        a.scope.add(c)

    return a


def create_test_token(user, application):

    now = timezone.now()
    expires = now + timedelta(days=1)
    t = AccessToken.objects.create(user=user, application=application,
                                   token="sample-token-string",
                                   expires=expires)
    return t


class Command(BaseCommand):
    help = 'Create a test user and application for the test client'

    def handle(self, *args, **options):
        g = create_group()
        # Delete any pre-existing BlueButton Scopes
        # print("Deleting pre-existing scope in the BlueButton group.")
        # ProtectedCapability.objects.filter(group=g).delete()
        #
        u = create_user(g)
        a = create_application(u, g)
        t = create_test_token(u, a)
        print("Name:", a.name)
        print("client_id:", a.client_id)
        print("client_secret:", a.client_secret)
        print("access_token:", t.token)
