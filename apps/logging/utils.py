"""
  Utility functions for logging
"""


def format_timestamp(dt):
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "") if dt is not None else None
