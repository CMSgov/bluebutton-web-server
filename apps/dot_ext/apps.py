from django.apps import AppConfig


class dot_extConfig(AppConfig):
    name = 'apps.dot_ext'
    label = 'dot_ext'
    verbose_name = 'Django OAuth Toolkit Extension'

    # def ready(self):
    #     from . import signals  # noqa
    def ready(self):
        print('=== dot_ext AppConfig.ready() called ===')
        from django.apps import apps

        try:
            m = apps.get_model('dot_ext', 'BlueButtonAccessToken')
            print('=== BlueButtonAccessToken found:', m, '===')
        except Exception as e:
            print('=== BlueButtonAccessToken NOT found:', e, '===')

        from . import signals  # noqa
