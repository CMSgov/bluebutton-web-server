"""Management command and shared functions to migrate fhir_id -> fhir_id_v2 and reverse.

Usage:
    forward: python manage.py migrate_fhir_id_to_v2
    reverse: python manage.py migrate_fhir_id_to_v2 --reverse

"""
from __future__ import annotations

from django.apps import apps as global_apps
from django.core.management.base import BaseCommand


def migrate_fhir_id_to_v2(apps=None, schema_editor=None) -> None:
    """Migrates crosswalk _fhir_id to fhir_id_v2. Run by the 0009 migration."""

    apps_mod = apps if apps is not None else global_apps
    Crosswalk = apps_mod.get_model('bluebutton', 'Crosswalk')
    for crosswalk in Crosswalk.objects.iterator(chunk_size=1000):
        if getattr(crosswalk, '_fhir_id', None):
            crosswalk.fhir_id_v2 = getattr(crosswalk, '_fhir_id') # type: ignore[attr-defined]
            crosswalk.save()

    ArchivedCrosswalk = apps_mod.get_model('bluebutton', 'ArchivedCrosswalk')
    for archived in ArchivedCrosswalk.objects.iterator(chunk_size=1000):
        if getattr(archived, '_fhir_id', None):
            archived.fhir_id_v2 = getattr(archived, '_fhir_id') # type: ignore[attr-defined]
            archived.save()


def reverse_migrate_v2_to_fhir_id(apps=None, schema_editor=None) -> None:
    """Reverse migration: copy fhir_id_v2 back to _fhir_id."""

    apps_mod = apps if apps is not None else global_apps
    Crosswalk = apps_mod.get_model('bluebutton', 'Crosswalk')
    for crosswalk in Crosswalk.objects.iterator(chunk_size=1000):
        if getattr(crosswalk, 'fhir_id_v2', None):
            crosswalk._fhir_id = getattr(crosswalk, 'fhir_id_v2') # type: ignore[attr-defined]
            crosswalk.save()

    ArchivedCrosswalk = apps_mod.get_model('bluebutton', 'ArchivedCrosswalk')
    for archived in ArchivedCrosswalk.objects.iterator(chunk_size=1000):
        if getattr(archived, 'fhir_id_v2', None):
            archived._fhir_id = getattr(archived, 'fhir_id_v2') # type: ignore[attr-defined]
            archived.save()


class Command(BaseCommand):
    help = 'Migrate values between _fhir_id and fhir_id_v2 (same logic as migration 0009)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reverse', 
            action='store_true', 
            dest='reverse', 
            default=False,
            help='Run the reverse migration (copy fhir_id_v2 -> _fhir_id)'
        )

    def handle(self, *args, **options):
        
        if options.get('reverse'):
            print('Running reverse_migrate_v2_to_fhir_id...')
            reverse_migrate_v2_to_fhir_id()
            print(self.style.SUCCESS('Reverse migration completed.'))
        else:
            print('Running migrate_fhir_id_to_v2...')
            migrate_fhir_id_to_v2()
            print(self.style.SUCCESS('Forward migration completed.'))
