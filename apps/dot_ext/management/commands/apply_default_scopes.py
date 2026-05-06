import os

from django.core.management.base import BaseCommand, CommandError

from apps.capabilities.models import ProtectedCapability
from apps.dot_ext.constants import BENE_PERSONAL_INFO_SCOPES
from apps.dot_ext.models import Application


class Command(BaseCommand):
    help = (
        'Ensure all apps have the appropriate default scopes. When '
        'require_demographic_scopes is False or None for an app, remove any '
        'demographic scopes set for that app.'
    )

    def _display_scopes(self, scopes, label):
        self.stdout.write(label)
        for scope in scopes:
            self.stdout.write(f' - {scope.slug}: {scope}')
        self.stdout.write()

    def handle(self, *args, **options):
        # TODO this seems too permissive, but TARGET_ENV doesn't seem to be set for
        # pr checks
        if os.getenv('TARGET_ENV') not in [None, 'local', 'test', 'sbx']:
            raise CommandError('Target environment not in [None, "local", "test", "sbx"].')

        # TODO is there a way to write this function more readably?
        default_scopes = ProtectedCapability.objects.filter(default__exact=True)
        # TODO what about demographic scopes that are not default?
        demographic_scopes = ProtectedCapability.objects.filter(slug__in=BENE_PERSONAL_INFO_SCOPES)
        default_non_demographic = default_scopes.difference(demographic_scopes)

        self._display_scopes(default_scopes, 'Default scopes:')
        self._display_scopes(demographic_scopes, 'Demographic scopes:')

        self.stdout.write('Applying changes to all apps.')

        added_count = 0
        removed_count = 0

        for app in Application.objects.all():
            before = set(app.scope.all())

            # TODO is there a way to only update those that need updating?
            if app.require_demographic_scopes:
                app.scope.add(*default_scopes)
            else:  # False or None
                app.scope.add(*default_non_demographic)
                app.scope.remove(*demographic_scopes)

            # TODO it is possible that another process could edit the scopes while
            # this command runs and then throw off these numbers
            after = set(app.scope.all())
            added = after.difference(before)
            removed = before.difference(after)
            if added:
                added_count += 1
            if removed:
                removed_count += 1

        self.stdout.write(f'Done. (Added scopes to {added_count} apps, removed scopes from {removed_count} apps.)')
