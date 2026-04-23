from django.core.management.base import BaseCommand

from apps.capabilities.models import ProtectedCapability
from apps.dot_ext.models import Application


class Command(BaseCommand):
    help = 'Ensure all apps have default scopes.'

    # TODO tests
    def handle(self, *args, **options):
        default_scopes = ProtectedCapability.objects.filter(default__exact=True)

        self.stdout.write('Default scopes:')
        for scope in default_scopes:
            self.stdout.write(f' - {scope}')

        self.stdout.write()
        self.stdout.write('Applying to all apps.')

        for app in Application.objects.all():
            # TODO is there a way to only update those that need updating?
            app.scope.add(*default_scopes)
            app.save()

        self.stdout.write('Done.')
