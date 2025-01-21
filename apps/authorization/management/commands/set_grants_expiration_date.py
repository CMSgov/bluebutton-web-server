import pytz

from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from apps.authorization.models import DataAccessGrant
from apps.dot_ext.models import Application
from dateutil.relativedelta import relativedelta


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
        parser.add_argument('--createdbefore', help="Datetime (UTC) when the grants created before this point of time are checked for update, "
                                                    "format: '%%m/%%d/%%y %%H:%%M:%%S', e.g. '01/16/25 19:58:26'.")
        parser.add_argument('--createdafter', help="Datetime (UTC) when the grants created after this point of time are checked for update, "
                                                   "format: '%%m/%%d/%%y %%H:%%M:%%S', e.g. '11/25/23 10:58:26'.")
        parser.add_argument('--dryrun', action='store_true', help="Dry run the command without making changes to the database.")
        parser.set_defaults(dryrun=False)

    def handle(self, *args, **options):
        app_name = None
        app_name_again = None
        turn_on_date = None

        # arguments validation
        if options['appname']:
            app_name = options['appname']

        if app_name is None:
            print("Error: appname required.")
            return False

        if options['appnameagain']:
            app_name_again = options['appnameagain']

        if app_name_again is None:
            print("Error: appnameagain required.")
            return False

        if (app_name != app_name_again):
            print("Error: appname does not match appnameagain.")
            return False

        # validate created before date
        created_before_date_str = None
        
        if options['createdbefore']:
            created_before_date_str = options['createdbefore']

        if created_before_date_str is None:
            print("Error: createdbefore required to repair grants.")
            return False

        created_before_date = None
        
        try:
            created_before_date = datetime.strptime(created_before_date_str, DATETIME_FMT).replace(tzinfo=timezone.utc)
        except ValueError as e:
            print("Error: bad date time value: {}".format(created_before_date_str))
            print(e)
            return False

        current_dt = datetime.now().replace(tzinfo=pytz.UTC)

        # time range must be a past time
        if created_before_date > current_dt:
            print("Error: createdbefore date must be a past time, createdbefore = {}, current date time ={}".format(created_before_date, current_dt))
            return False

        # validate created after date
        created_after_date_str = None

        if options['createdafter']:
            created_after_date_str = options['createdafter']

        if created_after_date_str is None:
            print("Error: createdafter required to repair grants.")
            return False

        created_after_date = None
        
        try:
            created_after_date = datetime.strptime(created_after_date_str, DATETIME_FMT).replace(tzinfo=timezone.utc)
        except ValueError as e:
            print("Error: bad date time value: {}".format(created_after_date_str))
            print(e)
            return False

        # validate date range
        if created_after_date > created_before_date:
            print("Error: createdbefore must >= createdafter : createdbefore = {}, createdafter = {}".format(created_before_date_str, created_after_date_str))
            return False
            
        dryrun = options['dryrun']

        if dryrun:
            print("Info: dryrun = {}, this is a dry run, no change to database.".format(dryrun))
            
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
            
        grants = DataAccessGrant.objects.filter(application=app.id).filter(expiration_date__isnull=True).filter(created_at__range=(created_after_date, created_before_date))
        print("process restriction: expiration_date = NULL and created_at in range: [{}, {}].".format(created_after_date, created_before_date))

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
