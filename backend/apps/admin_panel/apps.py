from django.apps import AppConfig


class AdminPanelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.apps.admin_panel"
    verbose_name = "Management panel"
