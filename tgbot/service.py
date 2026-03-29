"""
Telegram Bot service — synchronous helpers for sending messages from Django.
Uses python-telegram-bot's sync API for simplicity within Django views/signals.
"""
import logging
from functools import lru_cache

from django.conf import settings
from telegram import Bot
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_bot() -> Bot | None:
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not token:
        logger.warning('TELEGRAM_BOT_TOKEN not set — bot disabled')
        return None
    return Bot(token=token)


def send_message(chat_id: int | str, text: str, parse_mode=ParseMode.HTML) -> bool:
    bot = get_bot()
    if not bot:
        return False
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        loop.run_until_complete(bot.send_message(
            chat_id=chat_id, text=text, parse_mode=parse_mode,
        ))
        loop.close()
        return True
    except Exception as e:
        logger.error(f'Telegram send_message error: {e}')
        return False


def notify_admins(text: str) -> bool:
    chat_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '')
    if not chat_id:
        logger.warning('TELEGRAM_ADMIN_CHAT_ID not set')
        return False
    return send_message(chat_id, text)


# ── Order notifications ──────────────────────────────────

STATUS_EMOJI = {
    'pending': '\u23f3',       # hourglass
    'confirmed': '\u2705',     # green check
    'processing': '\U0001f4e6',  # package
    'shipped': '\U0001f69a',   # truck
    'delivered': '\U0001f389',  # party
    'cancelled': '\u274c',     # red X
}

STATUS_TEXT = {
    'pending': 'Ожидает подтверждения',
    'confirmed': 'Подтверждён',
    'processing': 'В обработке',
    'shipped': 'Отправлен',
    'delivered': 'Доставлен',
    'cancelled': 'Отменён',
}


def format_money(amount) -> str:
    return f'{int(amount):,}'.replace(',', ' ')


def notify_new_order(order) -> bool:
    """Send new order notification to admin chat."""
    items_text = ''
    for item in order.items.all():
        items_text += f'  \u2022 {item.product_name} ({item.size_name}/{item.color_name}) x{item.quantity} — {format_money(item.total_price)} сум\n'

    delivery = 'Самовывоз' if order.delivery_method == 'pickup' else 'Курьер'

    text = (
        f'\U0001f6d2 <b>Новый заказ #{order.order_number}</b>\n'
        f'\n'
        f'\U0001f464 {order.full_name}\n'
        f'\U0001f4de {order.phone}\n'
        f'\U0001f4e7 {order.email}\n'
        f'\n'
        f'\U0001f4e6 <b>Товары:</b>\n{items_text}\n'
        f'\U0001f69a Доставка: {delivery}\n'
    )
    if order.delivery_method == 'courier':
        text += f'\U0001f4cd {order.shipping_address}, {order.city}\n'
    elif order.pickup_point:
        text += f'\U0001f3ea {order.pickup_point.name}\n'

    if order.notes:
        text += f'\U0001f4dd {order.notes}\n'

    text += (
        f'\n'
        f'\U0001f4b0 <b>Итого: {format_money(order.total)} сум</b>'
    )

    return notify_admins(text)


def notify_order_status(order) -> bool:
    """Send order status update to customer via Telegram."""
    if not order.user or not order.user.telegram_id:
        return False

    emoji = STATUS_EMOJI.get(order.status, '\U0001f4e6')
    status_name = STATUS_TEXT.get(order.status, order.get_status_display())
    site_url = getattr(settings, 'SITE_URL', '')

    text = (
        f'{emoji} <b>Заказ #{order.order_number}</b>\n'
        f'\n'
        f'Статус: <b>{status_name}</b>\n'
    )

    if order.status == 'shipped':
        text += '\nВаш заказ уже в пути! Ожидайте доставку.\n'
    elif order.status == 'delivered':
        text += '\nСпасибо за покупку! Будем рады видеть вас снова.\n'
    elif order.status == 'cancelled':
        text += '\nЕсли у вас есть вопросы, свяжитесь с нами.\n'

    if site_url:
        text += f'\n<a href="{site_url}/orders/{order.order_number}/">Подробнее</a>'

    return send_message(order.user.telegram_id, text)