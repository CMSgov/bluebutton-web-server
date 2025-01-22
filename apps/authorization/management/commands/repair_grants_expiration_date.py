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
        'Repair Data Access Grant expiration_date for an app, '
        'pass in the app name whose grants need repair.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--appname', help="App name e.g. MyApp.")
        parser.add_argument('--appnameagain', help="Type app name again to confirm.")
        parser.add_argument('--turnondate', help="Datetime (UTC) when limit data access feature turned on for the app, "
                                                 "format: '%%m/%%d/%%Y %%H:%%M:%%S', e.g. '12/04/2024 15:58:26'.")
        parser.add_argument('--range', help="Datetime range (UTC) the grants checked for processing should be created in, "
                                                    "format: <begindate>-<enddate>, inclusive on both begin and end, "
                                                    "date format: %%m/%%d/%%y %%H:%%M:%%S, e.g. '01/16/25 19:58:26-01/18/25 23:59:59'.")
        parser.add_argument('--dryrun', action='store_true', help="Dry run the command without making changes to the database.")
        parser.set_defaults(dryrun=False)

    def handle(self, *args, **options):
        app_name = None
        turn_on_date = None

        # validate parameters
        result = validate_parameters(options, DATETIME_FMT, True)

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
        turn_on_date = result['turn_on_date']

        grants = DataAccessGrant.objects.filter(application=app.id).filter(created_at__range=(range_begin_date, range_end_date))
        print("process restriction: feature turned on date: {} and created_at in range: [{}, {}].".format(turn_on_date, range_begin_date, range_end_date))

        if grants.exists():
            print("Number of grants to be checked for repair = {}".format(len(grants)))
            processed = 0
            before_turn_on = 0
            after_turn_on = 0
            for grant in grants:
                processed = processed + 1
                # repair:
                if grant.created_at > turn_on_date:
                    print("+", end="")
                    after_turn_on = after_turn_on + 1
                    grant.expiration_date = grant.created_at.replace(tzinfo=pytz.UTC) + relativedelta(months=+13)
                else:
                    print("-", end="")
                    before_turn_on = before_turn_on + 1
                    grant.expiration_date = turn_on_date + relativedelta(months=+13)

                if not dryrun:
                    print("$", end="")
                    grant.save()
                else:
                    print("#", end="")
            print("")
            print("Processed grants: {}, created after feature turned on date: {}, created before turned on date: {}".format(processed, after_turn_on, before_turn_on))
        else:
            print("App {}, has no matching data access grants, command exits.".format(app.name))
