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

WAFFLE_FEATURE_FLAGS = (
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

        # Create feature flags for testing in local development
        for flag in WAFFLE_FEATURE_FLAGS:

            flag_obj = None

            try:
                flag_obj = Flag.objects.get(name=flag[0])
                self._log("Feature flag already exists: %s" % (str(flag_obj)))
            except Flag.DoesNotExist:
                flag_obj = Flag.objects.create(name=flag[0])
                self._log("Feature flag created: %s" % (str(flag[0])))

            if flag_obj:
                # further adding users
                if flag[1]:
                    for u in flag[1]:
                        try:
                            u = User.objects.get(username=u)
                            try:
                                flag_obj.users.add(u.id)
                                flag_obj.save()
                                self._log("User {} added to feature flag: {}".format(u, flag))
                            except Exception as e:
                                print(e)
                                self._log("Exception when adding user {} to feature flag: {}".format(u, flag))
                        except User.DoesNotExist:
                            # assuming test users exist before creating flags associated with them
                            self._log("User {} not found when adding it to feature flag: {}".format(u, flag))

    def _log(self, message):
        self.stdout.write(message)
