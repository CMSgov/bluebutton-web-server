from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'apps.core'
    label = 'core'
    verbose_name = 'Application Core'

    def ready(self):
        from . import signals  # noqa
