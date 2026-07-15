from django.apps import AppConfig


class ArticlesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.apps.articles"
    verbose_name = "News and weblog"
