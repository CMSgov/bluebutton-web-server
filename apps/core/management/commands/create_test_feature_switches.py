from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand
from waffle.models import Switch
from apps.core.models import Flag

WAFFLE_FEATURE_SWITCHES = (
    ("outreach_email", True),
    ("wellknown_applications", True),
    ("login", True),
    ("signup", True),
    ("require-scopes", True),
    ("testclient_v2", True),
    ("enable_testclient", True),
    ("show_testclient_link", True),
    ("interim-prod-access", True),
    ("enable_swaggerui", True),
)


class Command(BaseCommand):
    help = "Create Feature Switches/Flags for Local Testing"

    def handle(self, *args, **options):
        # Create feature switches for testing in local development
        for switch in WAFFLE_FEATURE_SWITCHES:
            try:
                Switch.objects.get(name=switch[0])
                self._log("Feature switch already exists: %s" % (str(switch)))
            except Switch.DoesNotExist:
                Switch.objects.create(name=switch[0], active=switch[1])
                self._log("Feature switch created: %s" % (str(switch)))

    def _log(self, message):
        self.stdout.write(message)
