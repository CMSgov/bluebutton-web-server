import logging
import logging.config
import re

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
SENSITIVE_DATA_FILTER = 'sensitive_data_filter'


def mask_if_has_mbi(text):
    return re.sub(MBI_PATTERN, '***MBI***', str(text), flags=re.VERBOSE)


def mask_with(func):
    def inner(value_to_mask):
        if isinstance(value_to_mask, str):
            return func(value_to_mask)

        if isinstance(value_to_mask, tuple):
            return tuple([func(arg) for arg in value_to_mask])

        if isinstance(value_to_mask, list):
            return [func(arg) for arg in value_to_mask]

        if isinstance(value_to_mask, dict):
            for key, value in value_to_mask.items():
                value_to_mask[key] = inner(value)

        return value_to_mask

    return inner


mask_mbi = mask_with(mask_if_has_mbi)


def _mask_erroring_database_rows(text):
    return re.sub(r'(?<=Failing row contains )\(.*\)', '***REDACTED***', str(text))


mask_erroring_database_rows = mask_with(_mask_erroring_database_rows)


class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        try:
            record.args = mask_mbi(record.args)
            record.msg = mask_mbi(record.msg)
            record.args = mask_erroring_database_rows(record.args)
            record.msg = mask_erroring_database_rows(record.msg)
            return True
        except Exception as e:
            raise e
