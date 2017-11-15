from __future__ import absolute_import
from __future__ import unicode_literals
from django.core.management.base import BaseCommand
from django.core.management import call_command
import os

__author__ = "Alan Viars"


def load_fixture():
    myfix = os.path.join(os.path.dirname(__file__), "fhir_server.json")
    print("Loading fixture @ ", myfix)
    call_command('loaddata', myfix)


class Command(BaseCommand):
    help = 'Create FHIR resource router and other FHIR tables'

    def handle(self, *args, **options):
        load_fixture()
