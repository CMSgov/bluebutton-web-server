"""
Project: bluebutton-web-server
App: apps/accounts/management/commands
FILE: review_usernames.py
Created: 12/07/19 8:12 PM

Created by: '@ekivemark'

review user accounts and identify format of usernames

"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_resourcerouter
from apps.dot_ext.models import Application
from apps.capabilities.models import ProtectedCapability
from oauth2_provider.models import AccessToken
from django.utils import timezone
from django.conf import settings
from django.db import models

# from apps.fhir.bluebutton.utils import get_fhir_now

import csv
import sys

import logging

logger = logging.getLogger('hhs_server.%s' % __name__)
CONFIRM_STRING = "FULL_REPORT"

class Command(BaseCommand):
    help = 'Report of users in BB2.0 API'

    def add_arguments(self, parser):
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
        outfile = kwargs['output_file']

        # quit unless we mean to run this command
        if confirm != CONFIRM_STRING:
            return

        # get the empty output file
        if not outfile:
            print("Please provide --output_file {path/to/filename}\nThe output file should be an empty or non-existent file used to report results")
            return

        # Prepare the output file
        out_list = []
        line = ["id", "username", "user_date_joined", "user_last_login",
                "user_is_staff", "user_is_superuser", "user_is_active","user_first_name", "user_last_name",
                "user_type", "assessment"]
        out_list.append(line)

        user = get_user_model()
        users = user.objects.all()

        for u in users:
            line = []
            u_id = u.id
            u_username = u.username
            u_joined = u.date_joined
            u_login = u.last_login
            u_first = u.first_name
            u_last = u.last_name
            u_super = u.is_super_user
            u_staff = u.is_staff
            u_active = u.is_active

            try:
                u_p = UserProfile.objects.get(user=u)
                u_role = u_p.user_type
            except UserProfile.DoesNotExist:
                u_role = ""

            if "@" in u_username:
                u_assess = "EMAIL"
            elif len(u_username) == 27:
                u_assess = "OLD_GUID"
            elif len(u_username) == 32:
                u_assess = "NEW GUID"
            else
                u_assess = "REVIEW"

            print("User=%s [%s %s]" % (u_username, u_first, u_last))

            # line = ["id", "username", "user_date_joined", "user_last_login",
            #         "user_is_staff", "user_is_superuser", "user_is_active", "user_first_name", "user_last_name"
            #         "user_type", "assessment"]

            # Build a line


            line = [u_id, u_username, u_joined, u_login,
                    u_staff, u_super, u_active, u_first, u_last,
                    u_role, u_assess]
            # append the line
            out_list.append(line)

        # We have processed all the guids so we will write the file out
        self.write_guid_report_csv(outfile, out_list)
