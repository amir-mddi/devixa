from django.apps import AppConfig
from django.db.models.signals import post_migrate


class SharedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dealio.apps.shared"

    def ready(self):
        import dealio.apps.common.check

        from dealio.apps.shared.initial_data.initial_data.project_config_initial import initialize_project_config

        def create_initial_project_config(sender, app_config, **kwargs):
            if app_config.name != self.name:
                return
            initialize_project_config()

        post_migrate.connect(
            create_initial_project_config,
            sender=self,
            dispatch_uid="shared.create_initial_project_config",
        )
