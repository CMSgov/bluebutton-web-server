from django.utils.decorators import available_attrs
from functools import wraps
from waffle import switch_is_active


def waffle_function_switch(switch_name):
    """ custom waffle switch for functions """
    def decorator(func):
        @wraps(func, assigned=available_attrs(func))
        def _wrapped_func(*args, **kwargs):
            if switch_name.startswith('!'):
                active = not switch_is_active(switch_name[1:])
            else:
                active = switch_is_active(switch_name)

            if not active:
                return
            return func(*args, **kwargs)
        return _wrapped_func
    return decorator
