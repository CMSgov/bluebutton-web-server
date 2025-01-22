import pytz

from datetime import datetime, timezone


# helper: parse a date time string into a UTC datetime obj
def _parse_date(key, d_str, d_fmt, err_msg, result):
    try:
        result[key] = datetime.strptime(d_str, d_fmt).replace(tzinfo=timezone.utc)
    except ValueError as e:
        print(err_msg)
        print(e)
        result['params_are_valid'] = False

# util to validate common parameters for grants repair
def validate_parameters(options, dt_fmt, check_turn_on_date):
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
        err_msg = "Error: bad date time value: {}".format(d_str)
        _parse_date("range_begin_date", d_str, dt_fmt, err_msg, result)
        if not result['params_are_valid']:
            return result
        d_str = r_value[1].strip()
        err_msg = "Error: bad date time value: {}".format(d_str)
        _parse_date("range_end_date", d_str, dt_fmt, err_msg, result)
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

    if check_turn_on_date:
        turn_on_date_str = None

        if options['turnondate']:
            turn_on_date_str = options['turnondate']

        if turn_on_date_str is None:
            print("Error: turnondate required to repair grants.")
            result['params_are_valid'] = False
            return result

        err_msg = "Error: bad date time value: {}".format(turn_on_date_str)
        _parse_date("turn_on_date", turn_on_date_str, dt_fmt, err_msg, result)
        if not result['params_are_valid']:
            return result

        turn_on_d = result['turn_on_date']
        if not (r_begin_d <= turn_on_d and turn_on_d <= r_end_d):
            print("Error: --turnondate {} must be in range [range_begin_date {}: range_end_date {}]".format(turn_on_d, r_begin_d, r_end_d))
            result['params_are_valid'] = False
            return result

    return result