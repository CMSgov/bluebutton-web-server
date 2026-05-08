from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = 'Adds include_samhsa column to oauth2_provider_accesstoken and records the migration'

    def handle(self, *args, **options):
        migration_app = 'dot_ext'
        migration_name = '0012_include_samhsa'

        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT COUNT(*) FROM django_migrations WHERE app = %s AND name = %s',
                [migration_app, migration_name]
            )
            already_applied = cursor.fetchone()[0] > 0
            print('already applied: ', already_applied)
            if already_applied:
                print('migration already applied - skipping')
                return

            # Add the column
            cursor.execute('''
                ALTER TABLE oauth2_provider_accesstoken
                ADD COLUMN IF NOT EXISTS include_samhsa boolean NOT NULL DEFAULT false;
            ''')

            # Record the migration
            cursor.execute(
                "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, %s)",
                [migration_app, migration_name, timezone.now()]
            )
