from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand
from waffle.models import Switch
from apps.core.models import Flag

WAFFLE_FEATURE_SWITCHES = (
    ("enable_coverage_only", True, "This enables the coverage-only use case."),
    ("enable_swaggerui", True, "This enables a page for the openapi docs and a link to the page from the main page."),
    ("enable_testclient", True, "This enables the test client."),
    ("expire_grant_endpoint", True, "This enables the /v<1/2>/o/expire_authenticated_user/<patient_id>/ endpoint."),
    ("login", True, "This enables login related URLs and code. See apps/accounts/urls.py file for more info."),
    ("logout", True, "This enables logout related URLs and code. See apps/accounts/urls.py file for more info."),
    ("outreach_email", True, "This enables developer outreach emails. Not active in prod."),
    ("require-scopes", True, "Thie enables enforcement of permission checking of scopes."),
    ("show_django_message_sdk", True, "This controls whether or not the 'what's new' message is shown in developer sandbox home."),
    ("show_testclient_link", True, "This controls the display of the test client link from the main page."),
    ("signup", True, "This enables signup related URLs and code paths. Not active in prod."),
    ("splunk_monitor", False, "This is used in other environments to ensure splunk forwarder is running."),
    ("v3_endpoints", True, "This enables v3 endpoints."),
    ("v3_testclient", True, "Enables v3 pathways in the testclient."),
    ("wellknown_applications", True, "This enables the /.well-known/applications end-point. Active in prod, but not in sbx/test."),
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
            except Switch.DoesNotExist:
                Switch.objects.create(name=switch[0], active=switch[1], note=switch[2])
                self._log("Feature switch created: %s" % (str(switch)))

        # Create feature flags for testing in local development
        for flag in WAFFLE_FEATURE_FLAGS:

            flag_obj = None

            try:
                flag_obj = Flag.objects.get(name=flag[0])
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
                                self._log("Exception when adding user {} to feature flag: {}".format(u, flag))
                        except User.DoesNotExist:
                            # assuming test users exist before creating flags associated with them
                            self._log("User {} not found when adding it to feature flag: {}".format(u, flag))

    def _log(self, message):
        self.stdout.write(message)
