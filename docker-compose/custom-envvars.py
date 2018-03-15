import os


def no_overwrite(env_var, env_val):
    """ Do not overwrite ENV VAR if it exists """
    check_for = os.environ.get(env_var)
    if check_for:
        # print("%s already set" % env_var)
        return
    else:
        # Not set
        os.environ.setdefault(env_var, env_val)
        # print("%s set to %s" % (env_var, env_val))
    return
