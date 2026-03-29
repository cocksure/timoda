"""
Telegram bot command handlers.
Run via: python manage.py tgbot
"""
import logging
import re

from django.conf import settings
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
    MenuButtonWebApp, WebAppInfo,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes,
)

logger = logging.getLogger(__name__)

WEBAPP_URL = ''

# Conversation states
LINK_WAITING = 1
REG_NAME = 2
REG_PHONE = 3
REG_EMAIL = 4
REG_CONFIRM = 5


def normalize_phone(phone: str) -> str:
    """Normalize phone: +998901234567"""
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('998') and len(digits) == 12:
        return f'+{digits}'
    if len(digits) == 9 and digits[0] == '9':
        return f'+998{digits}'
    return f'+{digits}' if digits else phone


# ── Commands ─────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start — greet user, show status."""
    from accounts.models import User

    tg_user = update.effective_user
    tg_id = tg_user.id

    # Check if already linked
    linked = False
    try:
        user = await User.objects.aget(telegram_id=tg_id)
        linked = True
        greeting = f'С возвращением, <b>{user.get_full_name()}</b>! \U0001f44b'
    except User.DoesNotExist:
        greeting = f'Привет, {tg_user.first_name}! \U0001f44b'

    text = (
        f'{greeting}\n\n'
        f'Я бот магазина <b>Timoda</b> — премиальный трикотаж.\n\n'
    )

    if linked:
        text += (
            f'\u2705 Аккаунт привязан\n\n'
            f'\U0001f4e6 /orders — ваши заказы\n'
            f'\u2753 /help — помощь\n'
        )
    else:
        text += (
            f'Что я умею:\n'
            f'\U0001f517 /link — привязать существующий аккаунт\n'
            f'\U0001f4dd /register — создать новый аккаунт\n'
            f'\U0001f4e6 /orders — ваши заказы\n'
            f'\u2753 /help — помощь\n'
        )

    keyboard = []
    if WEBAPP_URL.startswith('https://'):
        keyboard.append([InlineKeyboardButton(
            '\U0001f6cd Открыть магазин',
            web_app=WebAppInfo(url=WEBAPP_URL),
        )])

    if not linked:
        keyboard.append([
            InlineKeyboardButton('\U0001f517 Привязать аккаунт', callback_data='link'),
            InlineKeyboardButton('\U0001f4dd Регистрация', callback_data='register'),
        ])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_html(text, reply_markup=reply_markup)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        '<b>Команды:</b>\n\n'
        '/start — главное меню\n'
        '/link — привязать аккаунт Timoda\n'
        '/register — создать новый аккаунт\n'
        '/orders — список ваших заказов\n'
        '/unlink — отвязать аккаунт\n'
        '/help — эта справка\n'
    )
    if WEBAPP_URL.startswith('https://'):
        text += '\nНажмите кнопку «Магазин» чтобы перейти в каталог.'
    await update.message.reply_html(text)


async def cmd_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's recent orders."""
    from accounts.models import User
    from orders.models import Order

    tg_id = update.effective_user.id
    try:
        user = await User.objects.aget(telegram_id=tg_id)
    except User.DoesNotExist:
        await update.message.reply_html(
            'Аккаунт не привязан.\n/link — привязать\n/register — создать новый'
        )
        return

    orders = []
    async for o in Order.objects.filter(user=user).prefetch_related('items').order_by('-created_at')[:5]:
        orders.append(o)

    if not orders:
        await update.message.reply_html('У вас пока нет заказов. \U0001f6d2')
        return

    from tgbot.service import STATUS_EMOJI, STATUS_TEXT, format_money

    text = '<b>Ваши последние заказы:</b>\n\n'
    for o in orders:
        emoji = STATUS_EMOJI.get(o.status, '\U0001f4e6')
        status = STATUS_TEXT.get(o.status, o.status)
        text += (
            f'{emoji} <b>#{o.order_number}</b> — {format_money(o.total)} сум\n'
            f'    {status} | {o.created_at.strftime("%d.%m.%Y")}\n'
        )
        async for item in o.items.all():
            text += f'    \u2022 {item.product_name} ({item.size_name}/{item.color_name}) x{item.quantity}\n'
        text += '\n'

    keyboard = []
    if WEBAPP_URL.startswith('https://'):
        keyboard.append([InlineKeyboardButton(
            '\U0001f4cb Все заказы на сайте',
            web_app=WebAppInfo(url=f'{WEBAPP_URL}/orders/'),
        )])
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_html(text, reply_markup=reply_markup)


# ── Link account (conversation) ──────────────────────────

async def link_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start account linking — offer contact button."""
    from accounts.models import User

    # Handle both /link command and callback button
    if update.callback_query:
        await update.callback_query.answer()
        message = update.callback_query.message
        tg_id = update.callback_query.from_user.id
    else:
        message = update.message
        tg_id = update.effective_user.id

    # Already linked?
    try:
        user = await User.objects.aget(telegram_id=tg_id)
        await message.reply_html(
            f'\u2705 Аккаунт уже привязан: <b>{user.email}</b>\n'
            f'/unlink — отвязать'
        )
        return ConversationHandler.END
    except User.DoesNotExist:
        pass

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton('\U0001f4f1 Поделиться контактом', request_contact=True)]],
        one_time_keyboard=True, resize_keyboard=True,
    )
    await message.reply_html(
        '\U0001f517 <b>Привязка аккаунта</b>\n\n'
        'Нажмите кнопку ниже чтобы поделиться номером телефона, '
        'или отправьте <b>email</b> вручную.',
        reply_markup=keyboard,
    )
    return LINK_WAITING


async def link_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shared contact for linking."""
    contact = update.message.contact
    phone = normalize_phone(contact.phone_number)
    return await _try_link(update, phone)


async def link_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input (email or phone) for linking."""
    text = update.message.text.strip()
    return await _try_link(update, text)


async def _try_link(update: Update, identifier: str):
    """Try to find and link user by email or phone."""
    from accounts.models import User
    from django.db.models import Q

    tg_user = update.effective_user
    phone_normalized = normalize_phone(identifier)

    try:
        user = await User.objects.aget(
            Q(email__iexact=identifier) | Q(phone=identifier) | Q(phone=phone_normalized)
        )
    except User.DoesNotExist:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton('\U0001f4dd Зарегистрироваться', callback_data='register'),
        ]])
        await update.message.reply_html(
            '\u274c Аккаунт не найден.\n\n'
            'Проверьте данные или создайте новый аккаунт:',
            reply_markup=ReplyKeyboardRemove(),
        )
        await update.message.reply_html(
            'Нажмите кнопку ниже или /register',
            reply_markup=keyboard,
        )
        return ConversationHandler.END
    except User.MultipleObjectsReturned:
        await update.message.reply_html(
            'Найдено несколько аккаунтов. Уточните email.',
            reply_markup=ReplyKeyboardRemove(),
        )
        return LINK_WAITING

    if user.telegram_id and user.telegram_id != tg_user.id:
        await update.message.reply_html(
            '\u26a0\ufe0f Этот аккаунт уже привязан к другому Telegram.',
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    user.telegram_id = tg_user.id
    user.telegram_username = tg_user.username or ''
    await user.asave(update_fields=['telegram_id', 'telegram_username'])

    await update.message.reply_html(
        f'\u2705 Аккаунт <b>{user.email}</b> успешно привязан!\n\n'
        f'Теперь вы будете получать уведомления о заказах.',
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ── Register new account (conversation) ──────────────────

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start registration flow."""
    from accounts.models import User

    # Handle both /register command and callback button
    if update.callback_query:
        await update.callback_query.answer()
        message = update.callback_query.message
        tg_id = update.callback_query.from_user.id
    else:
        message = update.message
        tg_id = update.effective_user.id

    # Already linked?
    try:
        user = await User.objects.aget(telegram_id=tg_id)
        await message.reply_html(
            f'\u2705 У вас уже есть аккаунт: <b>{user.email}</b>'
        )
        return ConversationHandler.END
    except User.DoesNotExist:
        pass

    await message.reply_html(
        '\U0001f4dd <b>Регистрация в Timoda</b>\n\n'
        'Введите ваше <b>имя и фамилию</b>:\n'
        'Например: <code>Санжар Махмудов</code>'
    )
    return REG_NAME


async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive name, ask for phone."""
    name = update.message.text.strip()
    parts = name.split(maxsplit=1)
    context.user_data['reg_first_name'] = parts[0]
    context.user_data['reg_last_name'] = parts[1] if len(parts) > 1 else ''

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton('\U0001f4f1 Поделиться контактом', request_contact=True)]],
        one_time_keyboard=True, resize_keyboard=True,
    )
    await update.message.reply_html(
        f'Отлично, <b>{parts[0]}</b>! \U0001f44b\n\n'
        f'Теперь отправьте ваш <b>номер телефона</b>.\n'
        f'Нажмите кнопку ниже или введите вручную:',
        reply_markup=keyboard,
    )
    return REG_PHONE


async def register_phone_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive phone from shared contact."""
    contact = update.message.contact
    context.user_data['reg_phone'] = normalize_phone(contact.phone_number)
    return await _ask_email(update, context)


async def register_phone_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive phone from text input."""
    phone = normalize_phone(update.message.text.strip())
    if not re.match(r'^\+998\d{9}$', phone):
        await update.message.reply_html(
            '\u274c Неверный формат. Введите номер в формате:\n'
            '<code>+998901234567</code>'
        )
        return REG_PHONE
    context.user_data['reg_phone'] = phone
    return await _ask_email(update, context)


async def _ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        'Введите ваш <b>email</b>:\n'
        'Например: <code>sanjar@mail.com</code>',
        reply_markup=ReplyKeyboardRemove(),
    )
    return REG_EMAIL


async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive email, show confirmation."""
    from accounts.models import User

    email = update.message.text.strip().lower()

    # Simple email validation
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        await update.message.reply_html(
            '\u274c Неверный формат email. Попробуйте снова:'
        )
        return REG_EMAIL

    # Check if email exists
    if await User.objects.filter(email__iexact=email).aexists():
        await update.message.reply_html(
            '\u26a0\ufe0f Этот email уже зарегистрирован.\n'
            'Используйте /link чтобы привязать аккаунт.'
        )
        return ConversationHandler.END

    context.user_data['reg_email'] = email

    name = f"{context.user_data['reg_first_name']} {context.user_data.get('reg_last_name', '')}".strip()
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('\u2705 Подтвердить', callback_data='reg_confirm'),
            InlineKeyboardButton('\u274c Отмена', callback_data='reg_cancel'),
        ]
    ])
    await update.message.reply_html(
        f'\U0001f4cb <b>Проверьте данные:</b>\n\n'
        f'\U0001f464 Имя: <b>{name}</b>\n'
        f'\U0001f4f1 Телефон: <b>{context.user_data["reg_phone"]}</b>\n'
        f'\U0001f4e7 Email: <b>{email}</b>\n\n'
        f'Всё верно?',
        reply_markup=keyboard,
    )
    return REG_CONFIRM


async def register_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and create account."""
    query = update.callback_query
    await query.answer()

    if query.data == 'reg_cancel':
        await query.edit_message_text('Регистрация отменена.')
        context.user_data.clear()
        return ConversationHandler.END

    from accounts.models import User
    import secrets

    tg_user = query.from_user
    data = context.user_data

    # Create user
    password = secrets.token_urlsafe(12)
    user = await User.objects.acreate(
        username=f'tg_{tg_user.id}',
        email=data['reg_email'],
        first_name=data['reg_first_name'],
        last_name=data.get('reg_last_name', ''),
        phone=data['reg_phone'],
        telegram_id=tg_user.id,
        telegram_username=tg_user.username or '',
    )
    # Set password
    from django.contrib.auth.hashers import make_password
    user.password = make_password(password)
    await user.asave(update_fields=['password'])

    site_url = getattr(settings, 'SITE_URL', '')
    await query.edit_message_text(
        f'\u2705 <b>Аккаунт создан!</b>\n\n'
        f'\U0001f4e7 Email: <code>{data["reg_email"]}</code>\n'
        f'\U0001f511 Пароль: <code>{password}</code>\n\n'
        f'\u26a0\ufe0f Сохраните пароль! Он нужен для входа на сайте.\n'
        f'Вы уже будете получать уведомления о заказах.\n'
        + (f'\n\U0001f310 <a href="{site_url}">Перейти на сайт</a>' if site_url else ''),
        parse_mode='HTML',
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel any conversation."""
    context.user_data.clear()
    await update.message.reply_html(
        'Действие отменено.',
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ── Unlink ───────────────────────────────────────────────

async def cmd_unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unlink Telegram from account."""
    from accounts.models import User

    tg_id = update.effective_user.id
    try:
        user = await User.objects.aget(telegram_id=tg_id)
        user.telegram_id = None
        user.telegram_username = ''
        await user.asave(update_fields=['telegram_id', 'telegram_username'])
        await update.message.reply_html('\u2705 Аккаунт отвязан.')
    except User.DoesNotExist:
        await update.message.reply_html('Аккаунт не был привязан.')


# ── Location handler ─────────────────────────────────────

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save user's location for delivery."""
    from accounts.models import User

    tg_id = update.effective_user.id
    location = update.message.location

    try:
        user = await User.objects.aget(telegram_id=tg_id)
    except User.DoesNotExist:
        await update.message.reply_html(
            'Сначала привяжите аккаунт: /link или /register'
        )
        return

    # Save to user_data for future order
    context.user_data['latitude'] = location.latitude
    context.user_data['longitude'] = location.longitude

    await update.message.reply_html(
        f'\U0001f4cd <b>Геолокация получена</b>\n\n'
        f'Широта: {location.latitude:.6f}\n'
        f'Долгота: {location.longitude:.6f}\n\n'
        f'Эти координаты будут использованы при оформлении заказа.'
    )


# ── Callback queries ─────────────────────────────────────

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()


# ── Setup ────────────────────────────────────────────────

def create_application() -> Application:
    """Create and configure the bot application."""
    global WEBAPP_URL
    WEBAPP_URL = getattr(settings, 'TELEGRAM_WEBAPP_URL', '') or getattr(settings, 'SITE_URL', '')

    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise ValueError('TELEGRAM_BOT_TOKEN not set in .env')

    app = Application.builder().token(token).build()

    # Link conversation
    link_conv = ConversationHandler(
        entry_points=[
            CommandHandler('link', link_start),
            CallbackQueryHandler(link_start, pattern='^link$'),
        ],
        states={
            LINK_WAITING: [
                MessageHandler(filters.CONTACT, link_contact),
                MessageHandler(filters.TEXT & ~filters.COMMAND, link_text),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False,
    )

    # Register conversation
    register_conv = ConversationHandler(
        entry_points=[
            CommandHandler('register', register_start),
            CallbackQueryHandler(register_start, pattern='^register$'),
        ],
        states={
            REG_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_name),
            ],
            REG_PHONE: [
                MessageHandler(filters.CONTACT, register_phone_contact),
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone_text),
            ],
            REG_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_email),
            ],
            REG_CONFIRM: [
                CallbackQueryHandler(register_confirm, pattern='^reg_(confirm|cancel)$'),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False,
    )

    # Register handlers (order matters!)
    app.add_handler(link_conv)
    app.add_handler(register_conv)
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('help', cmd_help))
    app.add_handler(CommandHandler('orders', cmd_orders))
    app.add_handler(CommandHandler('unlink', cmd_unlink))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(CallbackQueryHandler(callback_handler))

    return app