"""
Management command to run the Telegram bot.

Usage:
    python manage.py tgbot              # run bot (polling, for local dev)
    python manage.py tgbot --setup      # set commands & menu button
    python manage.py tgbot --webhook    # set webhook (for production/PythonAnywhere)
    python manage.py tgbot --rmwebhook  # remove webhook (switch back to polling)
"""
import asyncio
import hashlib
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the Timoda Telegram bot'

    def add_arguments(self, parser):
        parser.add_argument(
            '--setup', action='store_true',
            help='Set bot commands and menu button, then exit',
        )
        parser.add_argument(
            '--webhook', action='store_true',
            help='Set Telegram webhook to SITE_URL/telegram/webhook/',
        )
        parser.add_argument(
            '--rmwebhook', action='store_true',
            help='Remove webhook (for switching to polling mode)',
        )

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stderr.write(self.style.ERROR(
                'TELEGRAM_BOT_TOKEN not set in .env — cannot start bot.'
            ))
            return

        if options['setup']:
            asyncio.run(self.setup_bot())
            return

        if options['webhook']:
            asyncio.run(self.set_webhook())
            return

        if options['rmwebhook']:
            asyncio.run(self.remove_webhook())
            return

        self.stdout.write(self.style.SUCCESS('Starting Timoda Telegram bot (polling)...'))
        from tgbot.handlers import create_application
        app = create_application()
        app.run_polling(drop_pending_updates=True)

    async def setup_bot(self):
        """Configure bot commands and menu button."""
        from telegram import Bot, BotCommand, MenuButtonWebApp, WebAppInfo

        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        webapp_url = settings.TELEGRAM_WEBAPP_URL or settings.SITE_URL

        # Set commands
        commands = [
            BotCommand('start', 'Главное меню'),
            BotCommand('register', 'Создать аккаунт'),
            BotCommand('link', 'Привязать аккаунт'),
            BotCommand('orders', 'Мои заказы'),
            BotCommand('lang', 'Язык / Til / Language'),
            BotCommand('unlink', 'Отвязать аккаунт'),
            BotCommand('help', 'Помощь'),
            BotCommand('cancel', 'Отмена'),
        ]
        await bot.set_my_commands(commands)
        self.stdout.write(self.style.SUCCESS('Bot commands set.'))

        # Set menu button → WebApp (requires HTTPS)
        if webapp_url and webapp_url.startswith('https://'):
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text='\U0001f6cd Магазин',
                    web_app=WebAppInfo(url=webapp_url),
                )
            )
            self.stdout.write(self.style.SUCCESS(f'Menu button set → {webapp_url}'))
        else:
            self.stdout.write(self.style.WARNING(
                'TELEGRAM_WEBAPP_URL must be HTTPS — menu button skipped.'
            ))

        info = await bot.get_me()
        self.stdout.write(self.style.SUCCESS(f'Bot: @{info.username} ({info.first_name})'))

    async def set_webhook(self):
        """Set Telegram webhook for production."""
        from telegram import Bot

        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        site_url = settings.SITE_URL

        if not site_url or not site_url.startswith('https://'):
            self.stderr.write(self.style.ERROR(
                'SITE_URL must be HTTPS for webhooks. Set it in .env'
            ))
            return

        webhook_url = f'{site_url}/telegram/webhook/'
        secret_token = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).hexdigest()[:32]

        await bot.set_webhook(
            url=webhook_url,
            secret_token=secret_token,
            drop_pending_updates=True,
        )
        self.stdout.write(self.style.SUCCESS(f'Webhook set → {webhook_url}'))

        info = await bot.get_webhook_info()
        self.stdout.write(f'  URL: {info.url}')
        self.stdout.write(f'  Pending updates: {info.pending_update_count}')

    async def remove_webhook(self):
        """Remove webhook to switch back to polling."""
        from telegram import Bot

        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.delete_webhook(drop_pending_updates=True)
        self.stdout.write(self.style.SUCCESS('Webhook removed. You can now use polling mode.'))