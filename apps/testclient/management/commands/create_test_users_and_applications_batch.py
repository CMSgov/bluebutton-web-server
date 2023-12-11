import pytz
import re
import time
import uuid

import apps.logging.request_logger as logging

from datetime import datetime, timedelta
from os import listdir
from random import randint, randrange, choice, sample
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError, ObjectDoesNotExist
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
from apps.mymedicare_cb.authorization import OAuth2ConfigSLSx

from apps.fhir.bluebutton.models import hash_hicn, hash_mbi

mymedicare_cb_logger = logging.getLogger(logging.AUDIT_AUTHN_MED_CALLBACK_LOGGER)
outreach_logger = logging.getLogger('hhs_server.apps.dot_ext.signals')

APPLICATION_SCOPES_FULL = ['patient/Patient.read', 'profile',
                           'patient/ExplanationOfBenefit.read', 'patient/Coverage.read',
                           'capability-a', 'capability-b']
APPLICATION_SCOPES_NON_DEMOGRAPHIC = ['patient/ExplanationOfBenefit.read',
                                      'patient/Coverage.read', 'capability-a', 'capability-b']
DEFAULT_BENE_COUNT = 100
DEFAULT_DEV_COUNT = 150
DEFAULT_MAX_APPS_PER_DEV = 5


def create_group(name="BlueButton"):

    g, created = Group.objects.get_or_create(name=name)
    if created:
        print("%s group created" % (name))
    else:
        print("%s group pre-existing. Create skipped." % (name))
    return g

# To avoid naming collisions when running this command more than once
def get_first_available_number(firstname):
    try:
        latest = User.objects.filter(
            first_name__contains=firstname).latest('first_name')
    except ObjectDoesNotExist:
        return 0
    # pull the number out of the name
    begin = ''.join(x for x in latest.first_name if x.isdigit())
    return int(begin) + 1

def create_dev_users_apps_and_bene_crosswalks(
        group,
        bene_count,
        dev_count,
        app_max,
        refresh_count,
        archived_count
):
    #
    # generate dev users dev0001, dev0002, dev0003 etc, with password, email, security questions, etc.
    # Counts are based on the inputs, but if undefined,will default to the defaults defined above
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
    begin_number = get_first_available_number("bene")

    for f in files:
        print("file={}".format(f))
        bene_rif = open('./synthetic-data/{}'.format(f), 'r')
        while True:
            if count == bene_count:
                break
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
                fn = "bene{}".format(count + begin_number)
                ln = "user{}".format(count + begin_number)

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
                    slsx_client = OAuth2ConfigSLSx(args)
                    try:
                        u = create_beneficiary_record(slsx_client, fhir_id)
                        date_picked = datetime.utcnow() - timedelta(days=randrange(700))
                        u.date_joined = date_picked.replace(tzinfo=pytz.utc)
                        u.save()
                        c = Crosswalk.objects.get(user=u)
                        c.created = u.date_joined
                        c.save()
                        bene_pk_list.append(u.pk)
                        synthetic_bene_cnt += 1
                        count += 1
                        print(".", end="", flush=True)
                        time.sleep(.05)
                    except ValidationError:
                        # If there is something wrong during 'create_beneficiary_record'
                        # i.e. 'user already exists', just try the next .rif record
                        continue
        bene_rif.close()
        file_cnt += 1
        print("RIF file processed = {}, synthetic bene generated = {}".format(file_cnt, synthetic_bene_cnt))
        if file_cnt >= 1:
            break

    # create dev users according dev-count parameter, default to 100
    # generate access tokens + refresh tokens + archived tokens for random picked benes for each app
    app_index = 0
    begin_number = get_first_available_number("DevUserFN")
    for i in range(dev_count):
        dev_u_fn = "DevUserFN{}".format(i + begin_number)
        dev_u_ln = "DevUserLN{}".format(i + begin_number)
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
        # apps per DEV user
        app_cnt = randint(1, app_max) if app_max > 0 else 0
        print(">>>>generating apps for user={}".format(u.username))
        for i in range(app_cnt):
            app_index += 1
            app_name = "app{}_{}".format(i, u)
            redirect_uri = "{}/testclient_{}/callback".format(settings.HOSTNAME_URL, app_name)
            if not(redirect_uri.startswith("http://") or redirect_uri.startswith("https://")):
                redirect_uri = "https://" + redirect_uri
            # 2% inactive, 5% opt out demo scopes
            # 10% public/implicit 90% confidential/authorization-code

            cl_type = "confidential"
            auth_grant_type = "authorization-code"

            if app_index % 10 == 0:
                cl_type = "public"
                auth_grant_type = "implicit"

            a = Application.objects.create(name=app_name,
                                           redirect_uris=redirect_uri,
                                           user=u,
                                           active=False if app_index % 50 == 0 else True,
                                           require_demographic_scopes=False if app_index % 20 == 0 else True,
                                           client_type=cl_type,
                                           authorization_grant_type=auth_grant_type)
            date_created = datetime.utcnow() - timedelta(days=randrange(700))
            a.created = date_created.replace(tzinfo=pytz.utc)
            u.date_joined = date_created - timedelta(days=randint(1, 10))
            u.save()
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
    # demo scope choice: 80% grant demo access, 20% deny demo access
    app_list = list(Application.objects.all())
    for bpk in bene_pk_list:
        seed = randint(1, 10)
        b = User.objects.get(pk=bpk)
        # check how many apps there are because there may be only 1
        # (caller can specify 0 for the app option)
        if seed <= 7 or len(app_list) == 1:
            # sign up to 1 app
            create_test_access_refresh_archived_tokens(
                b, choice(app_list), refresh_count, archived_count, seed)
        elif seed <= 9 and len(app_list) > 1:
            # sign up to 2 apps
            a2 = sample(app_list, 2)
            create_test_access_refresh_archived_tokens(
                b, a2[0], refresh_count, archived_count, seed)
            create_test_access_refresh_archived_tokens(
                b, a2[1], refresh_count, archived_count, seed)
        elif len(app_list) > 2:
            # sign up to 3 apps
            a3 = sample(app_list, 3)
            create_test_access_refresh_archived_tokens(
                b, a3[0], refresh_count, archived_count, seed)
            create_test_access_refresh_archived_tokens(
                b, a3[1], refresh_count, archived_count, seed)
            create_test_access_refresh_archived_tokens(
                b, a3[2], refresh_count, archived_count, seed)


def create_test_access_refresh_archived_tokens(
        user,
        application,
        refresh_count,
        archived_count,
        seed
):
    scope_all = ' '.join(APPLICATION_SCOPES_FULL)
    scope_no_demo = ' '.join(APPLICATION_SCOPES_NON_DEMOGRAPHIC)
    now = datetime.utcnow()
    expires = now + timedelta(days=10)

    # set scopes of at, ot: 80% grant demo info access, 20% deny
    if seed <= 8:
        scope = scope_all
    else:
        scope = scope_no_demo

    # a.created
    # u.created
    # update dates etc on at, rt, ot
    # at should be created later that a.created and b.created which ever the later
    # rt should be created about the same as at
    # ot should be later that at a random date
    ref_date = application.created if application.created > user.date_joined else user.date_joined
    date_created = ref_date + timedelta(days=1)

    at = AccessToken.objects.create(user=user, application=application,
                                    token=uuid.uuid4().hex,
                                    expires=expires.replace(tzinfo=pytz.utc),
                                    scope=scope)
    at.created = date_created.replace(tzinfo=pytz.utc)
    at.save()

    for i in range(refresh_count):
        rt = RefreshToken.objects.create(user=user, application=application,
                                     token=uuid.uuid4().hex)
        rt.created = at.created
        rt.save()

    # archived token: created, updated, archived_at datetime fields
    for i in range(archived_count):
        ot = ArchivedToken.objects.create(user=user,
                                      application=application,
                                      token=uuid.uuid4().hex,
                                      expires=expires.replace(tzinfo=pytz.utc),
                                      created=at.created,
                                      updated=at.created,
                                      archived_at=at.created,
                                      scope=scope)

        date_archived = ot.created + timedelta(days=10)
        ot.archived_at = date_archived.replace(tzinfo=pytz.utc)
        ot.save()


class Command(BaseCommand):
    help = ('Create dev users and create'
            ' apps for each of them, create bene users from '
            'synthetic data and crosswalk for each bene.')

    def add_arguments(self, parser):
        parser.add_argument("-b", "--bene-count", default=DEFAULT_BENE_COUNT,
                            help="Total number of bene to be created. "
                            "If none, defaults to {}.".format(DEFAULT_BENE_COUNT))
        parser.add_argument("-d", "--dev-count", default=DEFAULT_DEV_COUNT,
                            help="Total number of devs to be created. "
                            "If none, defaults to {}.". format(DEFAULT_DEV_COUNT))
        parser.add_argument("-a", "--app-max", default=DEFAULT_MAX_APPS_PER_DEV,
                            help="Maximum number of apps per dev. "
                            "If none, defaults to {}.".format(DEFAULT_MAX_APPS_PER_DEV))
        parser.add_argument("-r", "--refresh-tokens", default=1,
                            help="Refresh tokens per bene user. If none, defaults to 1.")
        parser.add_argument("-t", "--archived-tokens", default=1,
                            help="Archived tokens per bene user. If none, defaults to 1.")

    def handle(self, *args, **options):
        bene_count = int(options["bene_count"])
        dev_count = int(options["dev_count"])
        app_max = int(options["app_max"])
        refresh_tokens = int(options["refresh_tokens"])
        archived_tokens = int(options["archived_tokens"])
        g = create_group()
        create_dev_users_apps_and_bene_crosswalks(
            g,
            bene_count,
            dev_count,
            app_max,
            refresh_tokens,
            archived_tokens)
        # update grants
        update_grants()
