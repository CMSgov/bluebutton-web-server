"""
Project: bluebutton-web-server
App: apps.accounts.management.commands.
FILE: fix_permissions
Created: 3/14/18 3:59 PM

Created by: '@ekivemark'
"""
import sys

from django.contrib.auth.management import _get_all_permissions
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = "Fix permissions for all models, including proxy models."

    def handle(self, *args, **options):
        for model in apps.get_models():
            opts = model._meta
            sys.stdout.write('{}-{}\n'.format(opts.app_label, opts.object_name.lower()))
            ctype, created = ContentType.objects.get_or_create(
                app_label=opts.app_label,
                model=opts.object_name.lower())

            for codename, name in _get_all_permissions(opts):
                sys.stdout.write('  --{}\n'.format(codename))
                p, created = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=ctype,
                    defaults={'name': name})
                if created:
                    sys.stdout.write('Adding permission {}\n'.format(p))
