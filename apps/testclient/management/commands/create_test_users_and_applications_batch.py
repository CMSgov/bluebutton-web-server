import logging
import pytz
import re
import time
import uuid
from datetime import datetime, timedelta
from os import listdir
from random import randint, randrange, choice, sample
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from oauth2_provider.models import AccessToken, RefreshToken

from apps.accounts.models import UserProfile
from apps.fhir.bluebutton.models import Crosswalk
from apps.dot_ext.models import Application, ArchivedToken
from apps.capabilities.models import ProtectedCapability
from apps.authorization.models import update_grants
from apps.mymedicare_cb.models import create_beneficiary_record
from apps.fhir.bluebutton.models import hash_hicn, hash_mbi

mymedicare_cb_logger = logging.getLogger('audit.authenticate.mymedicare_cb')
outreach_logger = logging.getLogger('hhs_server.apps.dot_ext.signals')


def create_group(name="BlueButton"):

    g, created = Group.objects.get_or_create(name=name)
    if created:
        print("%s group created" % (name))
    else:
        print("%s group pre-existing. Create skipped." % (name))
    return g


def create_dev_users_apps_and_bene_crosswalks(group):
    #
    # generate dev users dev0001 - dev1000, with password, email, security questions, etc.
    # each dev user can have 1 to many applications: dev0001-app01, dev0001-app02
    # generate crosswalk bene users with FHIR-ID. HICN-HASH, MBI-HASH etc
    #

    # effectively turn off logging
    mymedicare_cb_logger.setLevel(logging.CRITICAL)
    outreach_logger.setLevel(logging.CRITICAL)

    bene_pk_list = []
    files = [f for f in listdir('./synthetic-data') if re.match(r'synthetic-beneficiary-.*\.rif', f)]
    count = 0
    file_cnt = 0
    synthetic_bene_cnt = 0
    for f in files:
        print("file={}".format(f))
        bene_rif = open('./synthetic-data/{}'.format(f), 'r')
        while True:
            line = bene_rif.readline()
            if not line:
                break
            if line.startswith('DML_IND|BENE_ID'):
                continue
            else:
                flds = line.split('|')
                fhir_id = flds[1]
                mbi = flds[14]
                hicn = flds[18]
                fn = "bene{}".format(count)
                ln = "user{}".format(count)
                count += 1
                # skip fred
                if fhir_id != '-20140000008325':
                    args = {
                        "username": str(uuid.uuid1()),
                        "user_hicn_hash": hash_hicn(hicn),
                        "user_mbi_hash": hash_mbi(mbi),
                        "user_id_type": "H",
                        "fhir_id": fhir_id,
                        "first_name": fn,
                        "last_name": ln,
                        "email": fn + '.' + ln + "@xyz.net",
                    }
                    u = create_beneficiary_record(**args)
                    date_picked = datetime.utcnow() - timedelta(days=randrange(700))
                    u.date_joined = date_picked.replace(tzinfo=pytz.utc)
                    u.save()
                    c = Crosswalk.objects.get(user=u)
                    c.created = u.date_joined
                    c.save()
                    bene_pk_list.append(u.pk)
                    synthetic_bene_cnt += 1
                    print(".", end="", flush=True)
                    time.sleep(.05)
                    if count > 8000:
                        break
        bene_rif.close()
        file_cnt += 1
        print("RIF file processed = {}, synthetic bene generated = {}".format(file_cnt, synthetic_bene_cnt))
        # if file_cnt >= 1:
        #     break

    # create 100 dev users
    # generate access tokens + refresh tokens + archived tokens for random picked benes for each app
    app_index = 0
    for i in range(50):
        dev_u_fn = "DevUserFN{}".format(i)
        dev_u_ln = "DevUserLN{}".format(i)
        u = User.objects.create_user(username="{}.{}".format(dev_u_fn, dev_u_ln),
                                     first_name=dev_u_fn,
                                     last_name=dev_u_ln,
                                     email='{}.{}@example.com'.format(dev_u_fn, dev_u_ln),
                                     password="THEP@ssw0rd{}".format(i),)
        UserProfile.objects.create(user=u,
                                   user_type="DEV",
                                   create_applications=True,
                                   organization_name=u.username + "ACME Inc.",
                                   password_reset_question_1='1',
                                   password_reset_answer_1='blue',
                                   password_reset_question_2='2',
                                   password_reset_answer_2='Frank',
                                   password_reset_question_3='3',
                                   password_reset_answer_3='Bentley')
        u.groups.add(group)
        # 1-5 apps per DEV user
        app_cnt = randint(1, 5)
        print(">>>>generating apps for user={}".format(u.username))
        for i in range(app_cnt):
            app_index += 1
            app_name = "app{}_{}".format(i, u)
            redirect_uri = "{}/testclient_{}/callback".format(settings.HOSTNAME_URL, app_name)
            if not(redirect_uri.startswith("http://") or redirect_uri.startswith("https://")):
                redirect_uri = "https://" + redirect_uri
            # 2% inactive, 5% opt out demo scopes
            a = Application.objects.create(name=app_name,
                                           redirect_uris=redirect_uri,
                                           user=u,
                                           active=False if app_index % 50 == 0 else True,
                                           require_demographic_scopes=False if app_index % 20 == 0 else True,
                                           client_type="confidential",
                                           authorization_grant_type="authorization-code")
            date_created = datetime.utcnow() - timedelta(days=randrange(700))
            a.created = date_created.replace(tzinfo=pytz.utc)
            a.save()
            titles = [
                "My Medicare and supplemental coverage information.",
                "My Medicare claim information.",
                "My general patient and demographic information.",
                "Profile information including name and email."
            ]

            for t in titles:
                c = ProtectedCapability.objects.get(title=t)
                a.scope.add(c)
        print("<<<<<generated apps for user={}".format(u.username))

    # go through benes: each bene sign up to 1, 2, 3 apps
    # most 70% 1 app, 25% 2 apps, 5% 3 apps
    app_list = list(Application.objects.all())
    for bpk in bene_pk_list:
        seed = randint(1, 10)
        b = User.objects.get(pk=bpk)
        if seed <= 7:
            # sign up to 1 app
            create_test_access_refresh_archived_tokens(b, choice(app_list))
        elif seed <= 9:
            # sign up to 2 apps
            a2 = sample(app_list, 2)
            create_test_access_refresh_archived_tokens(b, a2[0])
            create_test_access_refresh_archived_tokens(b, a2[1])
        else:
            # sign up to 3 apps
            a3 = sample(app_list, 3)
            create_test_access_refresh_archived_tokens(b, a3[0])
            create_test_access_refresh_archived_tokens(b, a3[1])
            create_test_access_refresh_archived_tokens(b, a3[2])


def create_test_access_refresh_archived_tokens(user, application):
    now = datetime.utcnow()
    expires = now + timedelta(days=10)

    scopes = application.scope.all()
    scope = []
    for s in scopes:
        scope.append(s.slug)
    # a.created
    # u.created
    # update dates etc on at, rt, ot
    # at should be created later that a.created and b.created which ever the later
    # rt should be created about the same as at
    # ot should be later that at a random date
    ref_date = application.created if application.created > user.date_joined else user.date_joined

    at = AccessToken.objects.create(user=user, application=application,
                                    token=uuid.uuid4().hex,
                                    expires=expires.replace(tzinfo=pytz.utc),
                                    scope=' '.join(scope))

    rt = RefreshToken.objects.create(user=user, application=application,
                                     token=uuid.uuid4().hex)

    date_created = ref_date + timedelta(days=1)
    at.created = date_created.replace(tzinfo=pytz.utc)
    at.save()
    rt.created = at.created
    rt.save()

    # archived token: created, updated, archived_at datetime fields
    ot = ArchivedToken.objects.create(user=user,
                                      application=application,
                                      token=uuid.uuid4().hex,
                                      expires=expires.replace(tzinfo=pytz.utc),
                                      created=at.created,
                                      updated=at.created,
                                      archived_at=at.created,
                                      scope=' '.join(scope))

    date_archived = ot.created + timedelta(days=10)
    ot.archived_at = date_archived.replace(tzinfo=pytz.utc)
    ot.save()

    return at, rt, ot


class Command(BaseCommand):
    help = ('Create 1000 dev user and create 1-5'
            ' apps for each of them, create 30k bene users from s3 bucket '
            'synthetic data and crosswalk for each bene.')

    def handle(self, *args, **options):
        g = create_group()
        create_dev_users_apps_and_bene_crosswalks(g)
        # update grants
        update_grants()
