from django.apps import AppConfig


class TgbotConfig(AppConfig):
    name = 'tgbot'
    default_auto_field = 'django.db.models.BigAutoField'
    verbose_name = 'Telegram бот'

    def ready(self):
        import tgbot.signals  # noqa: F401