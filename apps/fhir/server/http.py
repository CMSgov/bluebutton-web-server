"""
HTTP session helpers for calls to the BFD (FHIR) backend.

Each call gets its own session so no connection or session state is shared between requests.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from apps.fhir.server.settings import fhir_settings

# Only retry failures where the request never reached BFD (connection refused, DNS, connect timeout).
# Read and status retries are disabled so we never resend a request BFD may already be processing.
# read=False (not 0) re-raises the original read timeout so requests surfaces it as ReadTimeout.
BFD_RETRY = Retry(
    total=None,
    connect=3,
    read=False,
    status=0,
    other=0,
    backoff_factor=0.2,
    raise_on_status=False,
)


def bfd_session() -> requests.Session:
    """Return a new session with the BFD retry policy. Callers should close it when done."""
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=BFD_RETRY)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


def bfd_timeout() -> tuple:
    """(connect, read) timeout in seconds for BFD calls."""
    return (fhir_settings.connect_time, fhir_settings.wait_time)


def describe_request_error(e: requests.exceptions.RequestException) -> str:
    """Summarize a requests error without its URL, since BFD URLs contain patient identifiers."""
    inner = e.args[0] if e.args else None
    reason = getattr(inner, 'reason', inner)
    return f'{type(e).__name__}: {reason}'
