"""
Telegram bot command handlers with i18n (ru/uz/en).
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
from tgbot.texts import t

logger = logging.getLogger(__name__)

WEBAPP_URL = ''

# Conversation states
LINK_WAITING = 1
REG_NAME = 2
REG_PHONE = 3
REG_EMAIL = 4
REG_CONFIRM = 5


def normalize_phone(phone: str) -> str:
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('998') and len(digits) == 12:
        return f'+{digits}'
    if len(digits) == 9 and digits[0] == '9':
        return f'+998{digits}'
    return f'+{digits}' if digits else phone


async def get_lang(tg_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Get user language: from DB if linked, else from context."""
    from accounts.models import User
    try:
        user = await User.objects.aget(telegram_id=tg_id)
        return user.language or 'ru'
    except User.DoesNotExist:
        return context.user_data.get('lang', '')


async def get_linked_user(tg_id: int):
    from accounts.models import User
    try:
        return await User.objects.aget(telegram_id=tg_id)
    except User.DoesNotExist:
        return None


# ── Language selection ────────────────────────────────────

async def cmd_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection."""
    await _show_lang_picker(update.message)


async def _show_lang_picker(message):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('\U0001f1f7\U0001f1fa Русский', callback_data='lang_ru'),
            InlineKeyboardButton('\U0001f1fa\U0001f1ff O\'zbek', callback_data='lang_uz'),
            InlineKeyboardButton('\U0001f1ec\U0001f1e7 English', callback_data='lang_en'),
        ]
    ])
    await message.reply_html(
        '\U0001f30d <b>Выберите язык / Tilni tanlang / Choose language:</b>',
        reply_markup=keyboard,
    )


async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection callback."""
    query = update.callback_query
    await query.answer()

    lang = query.data.replace('lang_', '')  # ru, uz, en
    tg_id = query.from_user.id
    context.user_data['lang'] = lang

    # Save to DB if user is linked
    user = await get_linked_user(tg_id)
    if user:
        user.language = lang
        await user.asave(update_fields=['language'])

    await query.edit_message_text(t('lang_set', lang), parse_mode='HTML')

    # Show main menu after selecting language
    await cmd_start_inner(query.message, tg_id, query.from_user.first_name, lang, context)


# ── /start ────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    lang = await get_lang(tg_user.id, context)

    # First time? Show language picker
    if not lang:
        await _show_lang_picker(update.message)
        return

    await cmd_start_inner(update.message, tg_user.id, tg_user.first_name, lang, context)


async def cmd_start_inner(message, tg_id, first_name, lang, context):
    user = await get_linked_user(tg_id)
    linked = user is not None

    if linked:
        greeting = t('welcome_back', lang, name=user.get_full_name())
        menu = t('menu_linked', lang)
    else:
        greeting = t('welcome', lang, name=first_name)
        menu = t('menu_not_linked', lang)

    text = f'{greeting}\n\n{t("bot_intro", lang)}\n\n{menu}'

    keyboard = []
    if WEBAPP_URL.startswith('https://'):
        keyboard.append([InlineKeyboardButton(
            t('btn_open_shop', lang), web_app=WebAppInfo(url=WEBAPP_URL),
        )])
    if not linked:
        keyboard.append([
            InlineKeyboardButton(t('btn_link', lang), callback_data='link'),
            InlineKeyboardButton(t('btn_register', lang), callback_data='register'),
        ])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await message.reply_html(text, reply_markup=reply_markup)


# ── /help ─────────────────────────────────────────────────

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await get_lang(update.effective_user.id, context)
    await update.message.reply_html(t('help', lang or 'ru'))


# ── /orders ───────────────────────────────────────────────

async def cmd_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from orders.models import Order

    tg_id = update.effective_user.id
    lang = await get_lang(tg_id, context) or 'ru'
    user = await get_linked_user(tg_id)

    if not user:
        await update.message.reply_html(t('no_account', lang))
        return

    orders = []
    async for o in Order.objects.filter(user=user).prefetch_related('items').order_by('-created_at')[:5]:
        orders.append(o)

    if not orders:
        await update.message.reply_html(t('no_orders', lang))
        return

    from tgbot.service import STATUS_EMOJI, STATUS_TEXT, format_money

    text = t('your_orders', lang)
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
            t('btn_all_orders', lang),
            web_app=WebAppInfo(url=f'{WEBAPP_URL}/orders/'),
        )])
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_html(text, reply_markup=reply_markup)


# ── /link (conversation) ─────────────────────────────────

async def link_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        message = update.callback_query.message
        tg_id = update.callback_query.from_user.id
    else:
        message = update.message
        tg_id = update.effective_user.id

    lang = await get_lang(tg_id, context) or 'ru'
    context.user_data['lang'] = lang

    user = await get_linked_user(tg_id)
    if user:
        await message.reply_html(t('already_linked', lang, email=user.email))
        return ConversationHandler.END

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton(t('btn_share_contact', lang), request_contact=True)]],
        one_time_keyboard=True, resize_keyboard=True,
    )
    await message.reply_html(t('link_prompt', lang), reply_markup=keyboard)
    return LINK_WAITING


async def link_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = normalize_phone(update.message.contact.phone_number)
    return await _try_link(update, context, phone)


async def link_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _try_link(update, context, update.message.text.strip())


async def _try_link(update: Update, context, identifier: str):
    from accounts.models import User
    from django.db.models import Q

    tg_user = update.effective_user
    lang = context.user_data.get('lang', 'ru')
    phone_normalized = normalize_phone(identifier)

    try:
        user = await User.objects.aget(
            Q(email__iexact=identifier) | Q(phone=identifier) | Q(phone=phone_normalized)
        )
    except User.DoesNotExist:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(t('btn_register_new', lang), callback_data='register'),
        ]])
        await update.message.reply_html(
            t('user_not_found', lang), reply_markup=ReplyKeyboardRemove(),
        )
        await update.message.reply_html(
            t('btn_register_new', lang), reply_markup=keyboard,
        )
        return ConversationHandler.END
    except User.MultipleObjectsReturned:
        await update.message.reply_html(
            t('multiple_accounts', lang), reply_markup=ReplyKeyboardRemove(),
        )
        return LINK_WAITING

    if user.telegram_id and user.telegram_id != tg_user.id:
        await update.message.reply_html(
            t('already_linked_other', lang), reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    user.telegram_id = tg_user.id
    user.telegram_username = tg_user.username or ''
    user.language = lang
    await user.asave(update_fields=['telegram_id', 'telegram_username', 'language'])

    await update.message.reply_html(
        t('link_success', lang, email=user.email), reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ── /register (conversation) ─────────────────────────────

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        message = update.callback_query.message
        tg_id = update.callback_query.from_user.id
    else:
        message = update.message
        tg_id = update.effective_user.id

    lang = await get_lang(tg_id, context) or 'ru'
    context.user_data['lang'] = lang

    user = await get_linked_user(tg_id)
    if user:
        await message.reply_html(t('has_account', lang, email=user.email))
        return ConversationHandler.END

    await message.reply_html(t('reg_enter_name', lang))
    return REG_NAME


async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    name = update.message.text.strip()
    parts = name.split(maxsplit=1)
    context.user_data['reg_first_name'] = parts[0]
    context.user_data['reg_last_name'] = parts[1] if len(parts) > 1 else ''

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton(t('btn_share_contact', lang), request_contact=True)]],
        one_time_keyboard=True, resize_keyboard=True,
    )
    await update.message.reply_html(
        t('reg_enter_phone', lang, name=parts[0]), reply_markup=keyboard,
    )
    return REG_PHONE


async def register_phone_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_phone'] = normalize_phone(update.message.contact.phone_number)
    lang = context.user_data.get('lang', 'ru')
    await update.message.reply_html(t('reg_enter_email', lang), reply_markup=ReplyKeyboardRemove())
    return REG_EMAIL


async def register_phone_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    phone = normalize_phone(update.message.text.strip())
    if not re.match(r'^\+998\d{9}$', phone):
        await update.message.reply_html(t('reg_bad_phone', lang))
        return REG_PHONE
    context.user_data['reg_phone'] = phone
    await update.message.reply_html(t('reg_enter_email', lang), reply_markup=ReplyKeyboardRemove())
    return REG_EMAIL


async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from accounts.models import User

    lang = context.user_data.get('lang', 'ru')
    email = update.message.text.strip().lower()

    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        await update.message.reply_html(t('reg_bad_email', lang))
        return REG_EMAIL

    if await User.objects.filter(email__iexact=email).aexists():
        await update.message.reply_html(t('reg_email_exists', lang))
        return ConversationHandler.END

    context.user_data['reg_email'] = email
    name = f"{context.user_data['reg_first_name']} {context.user_data.get('reg_last_name', '')}".strip()

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(t('btn_confirm', lang), callback_data='reg_confirm'),
        InlineKeyboardButton(t('btn_cancel', lang), callback_data='reg_cancel'),
    ]])
    await update.message.reply_html(
        t('reg_confirm', lang, name=name, phone=context.user_data['reg_phone'], email=email),
        reply_markup=keyboard,
    )
    return REG_CONFIRM


async def register_confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'ru')

    if query.data == 'reg_cancel':
        await query.edit_message_text(t('reg_cancelled', lang))
        context.user_data.clear()
        return ConversationHandler.END

    from accounts.models import User
    from django.contrib.auth.hashers import make_password
    import secrets

    tg_user = query.from_user
    data = context.user_data

    password = secrets.token_urlsafe(12)
    user = await User.objects.acreate(
        username=f'tg_{tg_user.id}',
        email=data['reg_email'],
        first_name=data['reg_first_name'],
        last_name=data.get('reg_last_name', ''),
        phone=data['reg_phone'],
        telegram_id=tg_user.id,
        telegram_username=tg_user.username or '',
        language=lang,
    )
    user.password = make_password(password)
    await user.asave(update_fields=['password'])

    site_url = getattr(settings, 'SITE_URL', '')
    text = t('reg_success', lang, email=data['reg_email'], password=password)
    if site_url:
        text += f'\n\n<a href="{site_url}">{t("go_to_site", lang)}</a>'

    await query.edit_message_text(text, parse_mode='HTML')
    context.user_data.clear()
    return ConversationHandler.END


# ── /unlink ───────────────────────────────────────────────

async def cmd_unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    lang = await get_lang(tg_id, context) or 'ru'
    user = await get_linked_user(tg_id)
    if user:
        user.telegram_id = None
        user.telegram_username = ''
        await user.asave(update_fields=['telegram_id', 'telegram_username'])
        await update.message.reply_html(t('unlinked', lang))
    else:
        await update.message.reply_html(t('not_linked', lang))


# ── Location ──────────────────────────────────────────────

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    lang = await get_lang(tg_id, context) or 'ru'
    location = update.message.location

    user = await get_linked_user(tg_id)
    if not user:
        await update.message.reply_html(t('location_no_account', lang))
        return

    context.user_data['latitude'] = location.latitude
    context.user_data['longitude'] = location.longitude
    await update.message.reply_html(t('location_received', lang))


# ── Cancel ────────────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    context.user_data.clear()
    await update.message.reply_html(t('cancelled', lang), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ── Fallback callback handler ─────────────────────────────

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()


# ── Setup ─────────────────────────────────────────────────

def create_application() -> Application:
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
                CallbackQueryHandler(register_confirm_cb, pattern='^reg_(confirm|cancel)$'),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False,
    )

    # Register handlers
    app.add_handler(link_conv)
    app.add_handler(register_conv)
    app.add_handler(CallbackQueryHandler(lang_callback, pattern='^lang_'))
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('help', cmd_help))
    app.add_handler(CommandHandler('orders', cmd_orders))
    app.add_handler(CommandHandler('lang', cmd_lang))
    app.add_handler(CommandHandler('unlink', cmd_unlink))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(CallbackQueryHandler(callback_handler))

    return app