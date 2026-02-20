from types import SimpleNamespace

from apps.logging.utils import construct_quicksuite_logging_path
from apps.test import BaseApiTest


class TestLoggersGlobalMetricsManagementCommand(BaseApiTest):
    def test_construct_quicksuite_logging_normal(self):
        request = SimpleNamespace(
            session={"version": 3},
            path="/callback"
        )

        result = construct_quicksuite_logging_path(request)

        assert result == "v3/callback"

    def test_construct_quicksuite_logging_no_version(self):

        request = SimpleNamespace(
            session={},
            path="/callback"
        )

        result = construct_quicksuite_logging_path(request)

        assert result == "v/callback"

    def test_construct_quicksuite_logging_no_path(self):

        request = SimpleNamespace(
            session={"version": 3},
        )

        result = construct_quicksuite_logging_path(request)

        assert result == "v3"

    def test_construct_quicksuite_logging_no_request(self):

        request = None

        result = construct_quicksuite_logging_path(request)

        assert result == ""

    def test_construct_quicksuite_logging_no_session(self):

        request = SimpleNamespace(
            path="/callback"
        )

        result = construct_quicksuite_logging_path(request)

        print(result)

        assert result == "v/callback"
