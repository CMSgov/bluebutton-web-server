from django.apps import AppConfig


class LoggingConfig(AppConfig):
    name = 'apps.logging'
    label = 'logging'
    verbose_name = "Logging"

    def ready(self):
        from . import signals # noqa
