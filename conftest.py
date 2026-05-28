# import django
import pytest

# from django.conf import settings

# Ignore specific test files during collection
collect_ignore = ['scripts/medicare-test-synth-logins/test_medicare_logins.py']


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
