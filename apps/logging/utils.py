"""
  Utility functions for logging
"""


def format_timestamp(dt):
    '''
    Returns an ISO 6801 format string in UTC that works well with AWS Glue/Athena
    '''
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "") if dt is not None else None
