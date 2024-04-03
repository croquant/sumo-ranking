from django.apps import AppConfig


class RikishiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rikishi"

    def ready(self):
        from . import signals  # noqa: F401
