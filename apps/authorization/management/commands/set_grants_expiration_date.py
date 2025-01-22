import pytz

from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from apps.authorization.models import DataAccessGrant
from apps.dot_ext.models import Application
from dateutil.relativedelta import relativedelta
from .utils import validate_parameters


DATETIME_FMT = "%m/%d/%Y %H:%M:%S"
utc=pytz.UTC

class Command(BaseCommand):
    help = (
        'Set Data Access Grant expiration_date for an app, '
        'pass in the app name whose grants expiration_date missing and need a good value.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--appname', help="App name e.g. MyApp.")
        parser.add_argument('--appnameagain', help="Type app name again to confirm.")
        parser.add_argument('--range', help="Datetime range (UTC) the grants checked for processing should be created in, "
                                                    "format: <begindate>-<enddate>, inclusive on both begin and end, "
                                                    "date format: %%m/%%d/%%y %%H:%%M:%%S, e.g. '01/16/25 19:58:26-01/18/25 23:59:59'.")
        parser.add_argument('--dryrun', action='store_true', help="Dry run the command without making changes to the database.")
        parser.set_defaults(dryrun=False)

    def handle(self, *args, **options):
        # validate parameters
        result = validate_parameters(options, DATETIME_FMT, False)

        if not result['params_are_valid']:
            return False

        dryrun = options['dryrun']

        if dryrun:
            print("Info: dryrun = {}, this is a dry run, no change to database.".format(dryrun))
            
        app_name = result['app_name']

        apps = Application.objects.filter(name=app_name)

        if not apps.exists():
            print("Error: App {} not found.".format(app_name))
            return False

        app = apps.first()

        if app is None:
            print("Error: App '{}' not found".format(app_name))

        if not ("THIRTEEN_MONTH" in app.data_access_type):
            print("Error: This command only applies to app with THIRTEEN_MONTH data access type, '{}' data access type: {}.".format(app.name, app.data_access_type))
            return False

        range_begin_date = result['range_begin_date']
        range_end_date = result['range_end_date']

        grants = DataAccessGrant.objects.filter(application=app.id).filter(expiration_date__isnull=True).filter(created_at__range=(range_begin_date, range_end_date))
        print("process restriction: expiration_date = NULL and created_at in range: [{}, {}].".format(range_begin_date, range_end_date))

        if grants.exists():
            print("Number of grants to set expiration_date value = {}".format(len(grants)))
            processed = 0
            for grant in grants:
                print("+", end="")
                processed = processed + 1
                grant.expiration_date = grant.created_at.replace(tzinfo=pytz.UTC) + relativedelta(months=+13)
                if not dryrun:
                    print("$", end="")
                    grant.save()
                else:
                    print("#", end="")
            print("")
            print("processed grants: {}".format(processed))
        else:
            print("App {}, has no matching data access grants, command exits.".format(app.name))
