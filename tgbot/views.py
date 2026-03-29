"""
Webhook endpoint for Telegram bot (production mode).
For development, use polling: python manage.py tgbot
"""
import hashlib
import hmac
import json
import logging
import time

from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def webhook(request):
    """Handle incoming Telegram webhook updates."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return JsonResponse({'error': 'Bot not configured'}, status=503)

    # Verify secret token header
    secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
    expected_secret = hashlib.sha256(token.encode()).hexdigest()[:32]
    if secret != expected_secret:
        return HttpResponseForbidden('Invalid secret token')

    try:
        import asyncio
        from telegram import Update
        from tgbot.handlers import create_application

        data = json.loads(request.body)
        app = create_application()

        async def process():
            async with app:
                update = Update.de_json(data, app.bot)
                await app.process_update(update)

        asyncio.run(process())
    except Exception as e:
        logger.error(f'Webhook processing error: {e}')

    return JsonResponse({'ok': True})


def telegram_auth(request):
    """Verify Telegram Login Widget data and link/login user."""
    from accounts.models import User
    from django.contrib.auth import login
    from django.shortcuts import redirect

    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return HttpResponseForbidden('Bot not configured')

    # Collect and verify Telegram auth data
    data = {k: v for k, v in request.GET.items() if k != 'hash'}
    received_hash = request.GET.get('hash', '')

    check_string = '\n'.join(f'{k}={data[k]}' for k in sorted(data))
    secret_key = hashlib.sha256(token.encode()).digest()
    computed_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    if computed_hash != received_hash:
        return HttpResponseForbidden('Invalid auth data')

    # Check auth_date is recent (< 1 day)
    auth_date = int(data.get('auth_date', 0))
    if time.time() - auth_date > 86400:
        return HttpResponseForbidden('Auth data expired')

    tg_id = int(data['id'])
    tg_username = data.get('username', '')
    tg_first_name = data.get('first_name', '')
    tg_last_name = data.get('last_name', '')

    # Find or create user
    try:
        user = User.objects.get(telegram_id=tg_id)
    except User.DoesNotExist:
        if request.user.is_authenticated:
            user = request.user
            user.telegram_id = tg_id
            user.telegram_username = tg_username
            user.save(update_fields=['telegram_id', 'telegram_username'])
        else:
            email = f'tg_{tg_id}@telegram.user'
            user = User.objects.create_user(
                username=f'tg_{tg_id}',
                email=email,
                first_name=tg_first_name,
                last_name=tg_last_name,
                telegram_id=tg_id,
                telegram_username=tg_username,
            )

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('core:home')