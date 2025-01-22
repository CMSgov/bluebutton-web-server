import pytz

from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from apps.authorization.models import DataAccessGrant
from apps.dot_ext.models import Application
from dateutil.relativedelta import relativedelta


DATETIME_FMT = "%m/%d/%y %H:%M:%S"
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
                                                 "format: '%%m/%%d/%%y %%H:%%M:%%S', e.g. '12/04/24 15:58:26'.")
        parser.add_argument('--range', help="Datetime range (UTC) the grants checked for processing should be created in, "
                                                    "format: <begindate>-<enddate>, inclusive on both begin and end, "
                                                    "date format: %%m/%%d/%%y %%H:%%M:%%S, e.g. '01/16/25 19:58:26-01/18/25 23:59:59'.")
        parser.add_argument('--dryrun', action='store_true', help="Dry run the command without making changes to the database.")
        parser.set_defaults(dryrun=False)

    def handle(self, *args, **options):
        app_name = None
        turn_on_date = None

        # validate parameters
        result = validate_parameters(options, DATETIME_FMT)

        if not result['params_are_valid']:
            return False

        dryrun = options['dryrun']

        if dryrun:
            print("Info: dryrun = {}, this is a dry run, no change to database.".format(dryrun))
            
        app_name = result['app_name']

        apps = Application.objects.filter(name=app_name)

        if not apps.exists() or apps.first() is None:
            print("Error: App {} not found.".format(app_name))
            return False

        app = apps.first()

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
            skipped = 0
            before_turn_on = 0
            after_turn_on = 0
            for grant in grants:
                if turn_on_date is None and grant.expiration_date is not None:
                    print("0", end="")
                    skipped = skipped + 1
                    continue
                processed = processed + 1
                # repair:
                if turn_on_date is None or grant.created_at > turn_on_date:
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
            if ( skipped > 0 ):
                print("Skipped grants (already set): {}".format(skipped))
        else:
            print("App {}, has no matching data access grants, command exits.".format(app.name))

# helper: parse a date time string into a UTC datetime obj
def _parse_date(key, d_str, d_fmt, result):
    try:
        result[key] = datetime.strptime(d_str, d_fmt).replace(tzinfo=timezone.utc)
    except ValueError as e:
        print("Error: bad date time value: {}".format(d_str))
        print(e)
        result['params_are_valid'] = False

# util to validate common parameters for grants repair
def validate_parameters(options, dt_fmt):
    result = {
        'app_name': None,
        'turn_on_date': None,
        'range_begin_date': None,
        'range_end_date': None,
        'params_are_valid': True
    }

    # check app name
    if options['appname']:
        app_name = options['appname']

    if app_name is None:
        print("Error: appname required.")
        result['params_are_valid'] = False
        return result

    if options['appnameagain']:
        app_name_again = options['appnameagain']

    if app_name_again is None:
        print("Error: appnameagain required.")
        result['params_are_valid'] = False
        return result

    if (app_name != app_name_again):
        print("Error: appname does not match appnameagain.")
        result['params_are_valid'] = False
        return result

    result['app_name'] = app_name

    range_str = None

    if options['range']:
        range_str = options['range']

    if range_str is None:
        print("Error: --range requires a value, like: '01/16/25 19:58:26-01/18/25 23:59:59'.")
        result['params_are_valid'] = False
        return result

    r_value = range_str.split("-")
    if len(r_value) == 2:
        d_str = r_value[0].strip()
        _parse_date("range_begin_date", d_str, dt_fmt, result)
        if not result['params_are_valid']:
            return result
        d_str = r_value[1].strip()
        _parse_date("range_end_date", d_str, dt_fmt, result)
        if not result['params_are_valid']:
            return result
    else:
        print("Error: Malformed --range value, expecting value like: '01/16/25 19:58:26-01/18/25 23:59:59', received: {}.".format(range_str))
        result['params_are_valid'] = False
        return result
    
    current_dt = datetime.now().replace(tzinfo=pytz.UTC)
    r_end_d = result['range_end_date']
    # time range must be a past time, prohibit processing grants that just keep trickled in in an live ENV
    if r_end_d > current_dt:
        print("Error: --range end date must be a past time, range_end_date = {}, current date time ={}".format(r_end_d, current_dt))
        result['params_are_valid'] = False
        return result

    # validate date range
    r_begin_d = result['range_begin_date']

    if  r_begin_d > r_end_d:
        print("Error: --range value must be range_begin_date <= range_end_date: receiving range_begin_date = {}, range_end_date = {}".format(r_begin_d, r_end_d))
        result['params_are_valid'] = False
        return result

    turn_on_date_str = None

    if options['turnondate']:
        turn_on_date_str = options['turnondate']

    if turn_on_date_str is not None:
        _parse_date("turn_on_date", turn_on_date_str, dt_fmt, result)

        if not result['params_are_valid']:
            return result

        turn_on_d = result['turn_on_date']
        if ( turn_on_d >= current_dt ):
            print("Error: --range end date must be a past time, turn_on_date = {}, current date time ={}".format(turn_on_d, current_dt))
            result['params_are_valid'] = False
            return result

    return result