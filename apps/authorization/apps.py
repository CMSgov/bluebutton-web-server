from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuthorizationConfig(AppConfig):
    name = "apps.authorization"
    verbose_name = _("profiles")

    def ready(self):
        from . import signals  # noqa
