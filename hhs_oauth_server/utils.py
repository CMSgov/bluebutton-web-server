from decimal import Decimal

TRUE_LIST = [1, "1", "true", "True", "TRUE", "YES", "Yes", "yes", True]
FALSE_LIST = [0, "0", "False", "FALSE", "false", "NO", "No", "no", False]


def bool_env(env_val):
    """ check for boolean values """

    if env_val:
        if env_val in TRUE_LIST:
            return True
        if env_val in FALSE_LIST:
            return False
        return env_val
    else:
        if env_val in FALSE_LIST:
            return False

        return


def int_env(env_val):
    """ convert to integer from String """

    return int(Decimal(float(env_val)))
