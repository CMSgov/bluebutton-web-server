import re
import logging
import logging.config

MBI_WITH_HYPHEN_PATTERN = r"""\b
    [1-9](?![SLOIBZsloibz])[A-Za-z](?![SLOIBZsloibz)])[A-Za-z\d]\d
    -(?![SLOIBZsloibz])[A-Za-z](?![SLOIBZsloibz])[A-Za-z\d]\d
    -((?![SLOIBZsloibz])[A-Za-z]){2}\d{2}
    \b
    """

MBI_WITHOUT_HYPHEN_PATTERN = r"""\b
    [1-9](?![SLOIBZsloibz])[A-Za-z](?![SLOIBZsloibz)])[A-Za-z\d]\d
    (?![SLOIBZsloibz])[A-Za-z](?![SLOIBZsloibz])[A-Za-z\d]\d
    ((?![SLOIBZsloibzd])[A-Za-z]){2}\d{2}
    \b"""

MBI_PATTERN = f'({MBI_WITH_HYPHEN_PATTERN}|{MBI_WITHOUT_HYPHEN_PATTERN})'
SENSITIVE_DATA_FILTER = "sensitive_data_filter"


def has_mbi_match(text):
    return bool(re.search(MBI_PATTERN, text, flags=re.VERBOSE))


def mask_if_has_mbi(text):
    return re.sub(MBI_PATTERN, '***MBI***', str(text), flags=re.VERBOSE)


def is_not_primitive(value):
    primitive_types = (int, float, bool, str, bytes)
    return not isinstance(value, primitive_types)


def mask_mbi(value_to_mask):
    if isinstance(value_to_mask, str):
        return mask_if_has_mbi(value_to_mask)

    if isinstance(value_to_mask, tuple):
        return tuple([mask_if_has_mbi(arg) for arg in value_to_mask])

    if isinstance(value_to_mask, list):
        return [mask_if_has_mbi(arg) for arg in value_to_mask]

    if isinstance(value_to_mask, dict):
        for key, value in value_to_mask.items():
            if is_not_primitive(value):
                mask_mbi(value)
            else:
                value_to_mask[key] = mask_if_has_mbi(value)

    return value_to_mask


class SensitiveDataFilter(logging.Filter):

    def filter(self, record):
        try:
            record.args = mask_mbi(record.args)
            record.msg = mask_mbi(record.msg)
            return True
        except Exception:
            pass

    def mask_sensitive_args(self, args):
        if isinstance(args, dict):
            return mask_mbi(dict)

        return tuple([mask_if_has_mbi(arg) for arg in args])
