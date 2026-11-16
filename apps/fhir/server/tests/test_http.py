import socket
import threading
from unittest.mock import patch

import pytest
import requests
import urllib3.util.connection

from apps.fhir.server.http import BFD_RETRY, bfd_session, describe_request_error


def _closed_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@patch('urllib3.util.retry.time.sleep')
def test_connection_refused_is_retried(_mock_sleep):
    url = f'http://127.0.0.1:{_closed_port()}/v2/fhir/ExplanationOfBenefit/?patient=123'
    real_create_connection = urllib3.util.connection.create_connection

    with patch('urllib3.util.connection.create_connection', wraps=real_create_connection) as mock_connect:
        with bfd_session() as session, pytest.raises(requests.exceptions.ConnectionError) as exc_info:
            session.get(url, timeout=(1, 1))

    assert mock_connect.call_count == BFD_RETRY.connect + 1
    description = describe_request_error(exc_info.value)
    assert 'patient=123' not in description
    assert 'Connection refused' in description


def test_read_timeout_is_not_retried():
    accepted = []
    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    server.listen()
    stop = threading.Event()

    def accept_and_hang():
        server.settimeout(0.1)
        while not stop.is_set():
            try:
                conn, _ = server.accept()
                accepted.append(conn)
            except socket.timeout:
                continue

    thread = threading.Thread(target=accept_and_hang, daemon=True)
    thread.start()
    try:
        with bfd_session() as session, pytest.raises(requests.exceptions.ReadTimeout):
            session.get(f'http://127.0.0.1:{server.getsockname()[1]}/', timeout=(1, 0.2))
    finally:
        stop.set()
        thread.join()
        for conn in accepted:
            conn.close()
        server.close()

    assert len(accepted) == 1
