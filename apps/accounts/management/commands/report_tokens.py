"""
Project: bluebutton-web-server
App: apps/accounts/management/commands
FILE: report_tokens.py
Created: 12/07/19 8:12 PM

Created by: '@ekivemark'

Import csv file and report access/refresh tokens for users with shortened guids

"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_resourcerouter
from apps.dot_ext.models import Application
from apps.capabilities.models import ProtectedCapability
from oauth2_provider.models import AccessToken, RefreshToken
from django.utils import timezone
from django.conf import settings
from django.db import models

# from apps.fhir.bluebutton.utils import get_fhir_now

import csv
import sys

import logging

logger = logging.getLogger('hhs_server.%s' % __name__)
CONFIRM_STRING = "TOKEN_REPORT"

class Command(BaseCommand):
    help = 'Report access/refresh tokens for usernames with SLS collisions'

    def add_arguments(self, parser):
        parser.add_argument('--guid_file', type=str, help='absolute path to input file containing guids')
        parser.add_argument('--output_file', type=str, help='absolute path to output file containing reported items')
        parser.add_argument('--confirm', type=str, help='enter %s to confirm action' % CONFIRM_STRING)

    def read_guid_csv(self, guid_file):

        with open(guid_file, 'r') as f:
            reader = csv.reader(f)
            guid_list = list(reader)
        f.close()

        return guid_list

    def write_guid_report_csv(self, outfile, out_list):

        with open(outfile, 'w') as w:
            writer = csv.writer(w)
            writer.writerows(out_list)

        w.close()
        return

    def handle(self, *args, **kwargs):
        confirm = kwargs['confirm']
        guid_file = kwargs['guid_file']
        outfile = kwargs['output_file']

        # quit unless we mean to run this command
        if confirm != CONFIRM_STRING:
            return

        # Check we have the files we need
        # get the guid input file
        if not guid_file:
            print("Please provide --guid_file {path/to/filename}\nguid_file is a csv of usernames with no field header")
            return

        # get the empty output file
        if not outfile:
            print("Please provide --output_file {path/to/filename}\nThe output file should be an empty or non-existent file used to report results")
            return

        # Prepare the output file
        out_list = []
        line = ["id", "info_type",
                "username", "short_guid", "short_guid_line", "user_date_joined", "user_last_login",
                "user_is_staff", "user_is_superuser", "user_is_active","user_first_name", "user_last_name",
                "crosswalk_id", "crosswalk_fhir_id","crosswalk_hicn_hash", "crosswalk_date_created",
                "token_type", "token_id", "token_organization"]
        out_list.append(line)

        # get the guid_file
        guid_list = self.read_guid_csv(guid_file)

        ct = 1
        for i in guid_list:
            line = []
            info_type = "USER"
            token_id = ""
            token_application = ""
            user = get_user_model()
            try:
                u = user.objects.get(username=i)
                u_id = u.id
                u_username = u.username
                u_joined = u.date_joined
                u_login = u.last_login
                u_first = u.first_name
                u_last = u.last_name
                u_super = u.is_super_user
                u_staff = u.is_staff
                u_active = u.is_active
            except user.DoesNotExist:
                u_id = ""
                u_username = ""
                u_joined = ""
                u_login = ""
                u_first = ""
                u_last = ""
                u_super = ""
                u_staff = ""
                u_active = ""

            try:
                cx = Crosswalk.objects.get(user__username=i)
                cx_id = cx.id
                cx_user = cx.user
                cx_fhir = cx.fhir_id
                cx_hash = cx.user_id_hash
                cx_date = cx.date_created
            except Crosswalk.DoesNotExist:
                cx_id = ""
                cx_user = ""
                cx_fhir = ""
                cx_hash = ""
                cx_date = ""

            print("User=%s [%s %s] %s" % (u_username, u_first, u_last, cx_fhir))

            # line = ["id", "info_type",
            #         "username", "short_guid", "short_guid_line", "user_date_joined", "user_last_login",
            #         "user_is_staff", "user_is_superuser", "user_is_active", "user_first_name", "user_last_name",
            #         "crosswalk_id", "crosswalk_user", "crosswalk_fhir_id", "crosswalk_hicn_hash", "crosswalk_date_created",
            #         "token_id", "token_application"]

            token_id = ""
            token_application = ""
            # Build a line
            line = [u_id, info_type,
                    u_username, i, ct, u_joined, u_login,
                    u_staff, u_super, u_active, u_first, u_last,
                    cx_id, cx_user, cx_fhir, cx_hash, cx_date, token_id, token_application]
            # append the line
            out_list.append(line)

            try:
                a_token = AccessToken.objects.get(user__username=i)
                info_type = "ACCESS"
                for a in a_token:
                    token_id = a_token.id
                    token_application = a_token.application
                    line = [u_id, info_type,
                            u_username, i, ct, u_joined, u_login,
                            u_staff, u_super, u_active, u_first, u_last,
                            cx_id, cx_user, cx_fhir, cx_hash, cx_date, token_id, token_application]
                    # output the token info
                    out_list.append(line)
            except AccessToken.DoesNotExist:
                print("%s has no %s tokens" % (u_username,info_type))

            try:
                r_token = RefreshToken.objects.get(user__username=i)
                info_type = "REFRESH"
                for r in r_token:
                    token_id = r_token.id
                    token_application = r_token.application
                    line = [u_id, info_type,
                            u_username, i, ct, u_joined, u_login,
                            u_staff, u_super, u_active, u_first, u_last,
                            cx_id, cx_user, cx_fhir, cx_hash, cx_date, token_id, token_application]
                    # output the refresh info
                    out_list.append(line)
            except RefreshToken.DoesNotExist:
                print("%s has no %s tokens" % (u_username,info_type))

            ct += 1

        # We have processed all the guids so we will write the file out
        self.write_guid_report_csv(outfile, out_list)


