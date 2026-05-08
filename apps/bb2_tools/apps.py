from django.apps import AppConfig


class BB2ToolsConfig(AppConfig):
    name = 'apps.bb2_tools'
    label = 'bb2_tools'
    verbose_name = 'Blue Button 2.0 Tools'

    def ready(self):
        from . import admin as bb2_admin

        bb2_admin.register_models()
