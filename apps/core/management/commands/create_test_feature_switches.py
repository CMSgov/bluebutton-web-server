from django.core.management.base import BaseCommand
from waffle.models import Switch


class Command(BaseCommand):
    help = 'Create Feature Switches for Local Testing'

    def handle(self, *args, **options):
        # Create feature switches for testing in local development
        for switch in [['outreach_email', True],
                       ['wellknown_applications', True],
                       ['login', True],
                       ['signup', True]]:
            try:
                Switch.objects.get(name=switch[0])
                self._log('Feature switch already exists: %s' % (switch))
            except Switch.DoesNotExist:
                Switch.objects.create(name=switch[0], active=switch[1])
                self._log('Feature switch created: %s' % (switch))

    def _log(self, message):
        self.stdout.write(message)
