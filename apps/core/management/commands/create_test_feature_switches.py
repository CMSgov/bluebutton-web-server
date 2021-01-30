import os

from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand
from waffle.models import Switch

from apps.core.models import Flag

WAFFLE_FEATURE_SWITCHES = (('outreach_email', True),
                           ('wellknown_applications', True),
                           ('login', True),
                           ('signup', True),
                           ('require-scopes', True),
                           ('testclient_v2', True))


class Command(BaseCommand):
    help = 'Create Feature Switches/Flags for Local Testing'

    def handle(self, *args, **options):
        # Create feature switches for testing in local development
        for switch in WAFFLE_FEATURE_SWITCHES:
            try:
                Switch.objects.get(name=switch[0])
                self._log('Feature switch already exists: %s' % (str(switch)))
            except Switch.DoesNotExist:
                sw = switch[1]
                if switch[0] == "slsx-enable":
                    # override for now
                    SLSX_ENABLED = os.environ['SLSX_ENABLED']
                    if SLSX_ENABLED is not None and SLSX_ENABLED == "False":
                        sw = False
                    Switch.objects.create(name=switch[0], active=sw)
                    self._log('Feature switch created: %s' % (str((switch[0], sw))))
                else:
                    Switch.objects.create(name=switch[0], active=switch[1])
                    self._log('Feature switch created: %s' % (str(switch)))

        # Create feature flag bfd_v2
        flag_name = 'bfd_v2_flag'
        flag = None

        try:
            flag = Flag.objects.get(name=flag_name)
            self._log('Feature flag already exists: %s' % flag_name)
        except Flag.DoesNotExist:
            flag = Flag.objects.create(name=flag_name)
            self._log('Feature flag created: %s' % flag_name)

        bfd_v2_grp = Group.objects.get(name='BFDV2Partners')
        if bfd_v2_grp is not None:
            flag.groups.add(bfd_v2_grp)

        fred = User.objects.get(username="fred")
        if fred is not None:
            flag.users.add(fred)

    def _log(self, message):
        self.stdout.write(message)
