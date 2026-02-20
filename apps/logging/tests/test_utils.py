from types import SimpleNamespace

from apps.logging.utils import construct_quicksuite_logging_path
from apps.test import BaseApiTest


class TestLoggersGlobalMetricsManagementCommand(BaseApiTest):
    def test_construct_quicksuite_logging_normal(self):
        '''
        test path is properly formed with a version and a path
        '''
        request = SimpleNamespace(
            session={"version": 3},
            path="/callback"
        )

        result = construct_quicksuite_logging_path(request)

        assert result == "v3/callback"

    def test_construct_quicksuite_logging_no_version(self):
        '''
        test path doesn't have a version number if version doesn't exist
        '''

        request = SimpleNamespace(
            session={},
            path="/callback"
        )

        result = construct_quicksuite_logging_path(request)

        assert result == "v/callback"

    def test_construct_quicksuite_logging_no_path(self):
        '''
        test path only contains version number without a path_param
        '''

        request = SimpleNamespace(
            session={"version": 3},
        )

        result = construct_quicksuite_logging_path(request)

        assert result == "v3"

    def test_construct_quicksuite_logging_no_request(self):
        '''
        test path is empty if request doesn't exist
        '''

        request = None

        result = construct_quicksuite_logging_path(request)

        assert result == ""

    def test_construct_quicksuite_logging_no_session(self):
        '''
        test path doesn't have a version number if session doesn't exist
        '''

        request = SimpleNamespace(
            path="/callback"
        )

        result = construct_quicksuite_logging_path(request)

        assert result == "v/callback"
