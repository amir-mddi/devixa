from django.apps import AppConfig


class SharedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dealio.apps.shared'

    def ready(self):
        import dealio.apps.common.check