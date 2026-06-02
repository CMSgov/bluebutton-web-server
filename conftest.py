# import django
import pytest

# Ignore specific test files during collection
collect_ignore = [
    'scripts/medicare-test-synth-logins/test_medicare_logins.py',
    'apps/integration_tests/logging_tests.py',
    'apps/integration_tests/selenium_accounts_tests.py',
    'apps/integration_tests/selenium_spanish_tests.py',
    'apps/integration_tests/selenium_tests.py',
]


def pytest_configure(config):
    """Ensure Django is fully set up before any test collection or execution."""
    import django

    django.setup()


@pytest.fixture
def enable_switch():
    """Fixture to activate a waffle switch for a test."""
    from waffle.testutils import override_switch

    def _enable(switch_name, active=True):
        return override_switch(switch_name, active=active)

    return _enable


# @pytest.fixture(scope='session')
# def django_db_use_migrations():
#     return True
