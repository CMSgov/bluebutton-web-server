from waffle import switch_is_active


def switch_value(switch_name, value, default):
    if switch_name.startswith('!'):
        active = not switch_is_active(switch_name[1:])
    else:
        active = switch_is_active(switch_name)

    if active:
        return value

    return default
