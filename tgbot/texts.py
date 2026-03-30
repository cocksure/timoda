"""
Bot message translations: ru, uz, en
"""

TEXTS = {
    # ── Language selection ────────────────────────────────
    'choose_lang': {
        'ru': '\U0001f30d <b>Выберите язык:</b>',
        'uz': "\U0001f30d <b>Tilni tanlang:</b>",
        'en': '\U0001f30d <b>Choose language:</b>',
    },
    'lang_set': {
        'ru': '\u2705 Язык установлен: <b>Русский</b>',
        'uz': "\u2705 Til tanlandi: <b>O'zbek</b>",
        'en': '\u2705 Language set: <b>English</b>',
    },

    # ── /start ────────────────────────────────────────────
    'welcome_back': {
        'ru': 'С возвращением, <b>{name}</b>! \U0001f44b',
        'uz': 'Qaytganingizdan xursandmiz, <b>{name}</b>! \U0001f44b',
        'en': 'Welcome back, <b>{name}</b>! \U0001f44b',
    },
    'welcome': {
        'ru': 'Привет, {name}! \U0001f44b',
        'uz': 'Salom, {name}! \U0001f44b',
        'en': 'Hi, {name}! \U0001f44b',
    },
    'bot_intro': {
        'ru': 'Я бот магазина <b>Timoda</b> — премиальный трикотаж.',
        'uz': 'Men <b>Timoda</b> do\'koni boti — premium trikotaj.',
        'en': 'I\'m the <b>Timoda</b> store bot — premium knitwear.',
    },
    'menu_linked': {
        'ru': (
            '\u2705 Аккаунт привязан\n\n'
            '\U0001f4e6 /orders — ваши заказы\n'
            '\U0001f30d /lang — сменить язык\n'
            '\u2753 /help — помощь'
        ),
        'uz': (
            '\u2705 Akkaunt ulangan\n\n'
            '\U0001f4e6 /orders — buyurtmalaringiz\n'
            '\U0001f30d /lang — tilni o\'zgartirish\n'
            '\u2753 /help — yordam'
        ),
        'en': (
            '\u2705 Account linked\n\n'
            '\U0001f4e6 /orders — your orders\n'
            '\U0001f30d /lang — change language\n'
            '\u2753 /help — help'
        ),
    },
    'menu_not_linked': {
        'ru': (
            '\U0001f517 /link — привязать аккаунт\n'
            '\U0001f4dd /register — создать аккаунт\n'
            '\U0001f4e6 /orders — заказы\n'
            '\U0001f30d /lang — сменить язык\n'
            '\u2753 /help — помощь'
        ),
        'uz': (
            '\U0001f517 /link — akkauntni ulash\n'
            '\U0001f4dd /register — akkaunt yaratish\n'
            '\U0001f4e6 /orders — buyurtmalar\n'
            '\U0001f30d /lang — tilni o\'zgartirish\n'
            '\u2753 /help — yordam'
        ),
        'en': (
            '\U0001f517 /link — link your account\n'
            '\U0001f4dd /register — create account\n'
            '\U0001f4e6 /orders — orders\n'
            '\U0001f30d /lang — change language\n'
            '\u2753 /help — help'
        ),
    },
    'btn_open_shop': {
        'ru': '\U0001f6cd Открыть магазин',
        'uz': '\U0001f6cd Do\'konni ochish',
        'en': '\U0001f6cd Open shop',
    },
    'btn_link': {
        'ru': '\U0001f517 Привязать аккаунт',
        'uz': '\U0001f517 Akkauntni ulash',
        'en': '\U0001f517 Link account',
    },
    'btn_register': {
        'ru': '\U0001f4dd Регистрация',
        'uz': '\U0001f4dd Ro\'yxatdan o\'tish',
        'en': '\U0001f4dd Register',
    },

    # ── /help ─────────────────────────────────────────────
    'help': {
        'ru': (
            '<b>Команды:</b>\n\n'
            '/start — главное меню\n'
            '/register — создать аккаунт\n'
            '/link — привязать аккаунт\n'
            '/orders — мои заказы\n'
            '/lang — сменить язык\n'
            '/unlink — отвязать аккаунт\n'
            '/help — помощь'
        ),
        'uz': (
            '<b>Buyruqlar:</b>\n\n'
            '/start — asosiy menyu\n'
            '/register — akkaunt yaratish\n'
            '/link — akkauntni ulash\n'
            '/orders — buyurtmalarim\n'
            '/lang — tilni o\'zgartirish\n'
            '/unlink — akkauntni ajratish\n'
            '/help — yordam'
        ),
        'en': (
            '<b>Commands:</b>\n\n'
            '/start — main menu\n'
            '/register — create account\n'
            '/link — link account\n'
            '/orders — my orders\n'
            '/lang — change language\n'
            '/unlink — unlink account\n'
            '/help — help'
        ),
    },

    # ── /orders ───────────────────────────────────────────
    'no_account': {
        'ru': 'Аккаунт не привязан.\n/link — привязать\n/register — создать новый',
        'uz': 'Akkaunt ulanmagan.\n/link — ulash\n/register — yangi yaratish',
        'en': 'Account not linked.\n/link — link\n/register — create new',
    },
    'no_orders': {
        'ru': 'У вас пока нет заказов. \U0001f6d2',
        'uz': 'Hali buyurtmalaringiz yo\'q. \U0001f6d2',
        'en': 'No orders yet. \U0001f6d2',
    },
    'your_orders': {
        'ru': '<b>Ваши последние заказы:</b>\n\n',
        'uz': '<b>So\'nggi buyurtmalaringiz:</b>\n\n',
        'en': '<b>Your recent orders:</b>\n\n',
    },
    'btn_all_orders': {
        'ru': '\U0001f4cb Все заказы на сайте',
        'uz': '\U0001f4cb Barcha buyurtmalar saytda',
        'en': '\U0001f4cb All orders on site',
    },

    # ── /link ─────────────────────────────────────────────
    'already_linked': {
        'ru': '\u2705 Аккаунт уже привязан: <b>{email}</b>\n/unlink — отвязать',
        'uz': '\u2705 Akkaunt allaqachon ulangan: <b>{email}</b>\n/unlink — ajratish',
        'en': '\u2705 Account already linked: <b>{email}</b>\n/unlink — unlink',
    },
    'link_prompt': {
        'ru': (
            '\U0001f517 <b>Привязка аккаунта</b>\n\n'
            'Нажмите кнопку ниже чтобы поделиться номером телефона, '
            'или отправьте <b>email</b> вручную.'
        ),
        'uz': (
            '\U0001f517 <b>Akkauntni ulash</b>\n\n'
            'Telefon raqamingizni ulashish uchun quyidagi tugmani bosing '
            'yoki <b>email</b> kiriting.'
        ),
        'en': (
            '\U0001f517 <b>Link account</b>\n\n'
            'Tap the button below to share your phone number, '
            'or send your <b>email</b> manually.'
        ),
    },
    'btn_share_contact': {
        'ru': '\U0001f4f1 Поделиться контактом',
        'uz': '\U0001f4f1 Kontaktni ulashish',
        'en': '\U0001f4f1 Share contact',
    },
    'user_not_found': {
        'ru': '\u274c Аккаунт не найден.\nПроверьте данные или создайте новый аккаунт:',
        'uz': '\u274c Akkaunt topilmadi.\nMa\'lumotlarni tekshiring yoki yangi akkaunt yarating:',
        'en': '\u274c Account not found.\nCheck your info or create a new account:',
    },
    'already_linked_other': {
        'ru': '\u26a0\ufe0f Этот аккаунт уже привязан к другому Telegram.',
        'uz': '\u26a0\ufe0f Bu akkaunt boshqa Telegramga ulangan.',
        'en': '\u26a0\ufe0f This account is linked to another Telegram.',
    },
    'link_success': {
        'ru': '\u2705 Аккаунт <b>{email}</b> успешно привязан!\n\nТеперь вы будете получать уведомления о заказах.',
        'uz': '\u2705 <b>{email}</b> akkaunt muvaffaqiyatli ulandi!\n\nEndi buyurtmalar haqida xabar olasiz.',
        'en': '\u2705 Account <b>{email}</b> linked!\n\nYou will now receive order notifications.',
    },
    'unlinked': {
        'ru': '\u2705 Аккаунт отвязан.',
        'uz': '\u2705 Akkaunt ajratildi.',
        'en': '\u2705 Account unlinked.',
    },
    'not_linked': {
        'ru': 'Аккаунт не был привязан.',
        'uz': 'Akkaunt ulanmagan edi.',
        'en': 'Account was not linked.',
    },

    # ── /register ─────────────────────────────────────────
    'has_account': {
        'ru': '\u2705 У вас уже есть аккаунт: <b>{email}</b>',
        'uz': '\u2705 Sizda allaqachon akkaunt bor: <b>{email}</b>',
        'en': '\u2705 You already have an account: <b>{email}</b>',
    },
    'reg_enter_name': {
        'ru': '\U0001f4dd <b>Регистрация в Timoda</b>\n\nВведите ваше <b>имя и фамилию</b>:\nНапример: <code>Санжар Махмудов</code>',
        'uz': '\U0001f4dd <b>Timoda\'da ro\'yxatdan o\'tish</b>\n\n<b>Ism va familiyangizni</b> kiriting:\nMasalan: <code>Sanjar Maxmudov</code>',
        'en': '\U0001f4dd <b>Register at Timoda</b>\n\nEnter your <b>full name</b>:\nExample: <code>John Doe</code>',
    },
    'reg_enter_phone': {
        'ru': 'Отлично, <b>{name}</b>! \U0001f44b\n\nТеперь отправьте ваш <b>номер телефона</b>.\nНажмите кнопку ниже или введите вручную:',
        'uz': 'Ajoyib, <b>{name}</b>! \U0001f44b\n\nEndi <b>telefon raqamingizni</b> yuboring.\nQuyidagi tugmani bosing yoki qo\'lda kiriting:',
        'en': 'Great, <b>{name}</b>! \U0001f44b\n\nNow send your <b>phone number</b>.\nTap the button below or type it manually:',
    },
    'reg_bad_phone': {
        'ru': '\u274c Неверный формат. Введите номер в формате:\n<code>+998901234567</code>',
        'uz': '\u274c Noto\'g\'ri format. Raqamni kiriting:\n<code>+998901234567</code>',
        'en': '\u274c Invalid format. Enter number like:\n<code>+998901234567</code>',
    },
    'reg_enter_email': {
        'ru': 'Введите ваш <b>email</b>:\nНапример: <code>sanjar@mail.com</code>',
        'uz': '<b>Email</b>ingizni kiriting:\nMasalan: <code>sanjar@mail.com</code>',
        'en': 'Enter your <b>email</b>:\nExample: <code>sanjar@mail.com</code>',
    },
    'reg_bad_email': {
        'ru': '\u274c Неверный формат email. Попробуйте снова:',
        'uz': '\u274c Email formati noto\'g\'ri. Qaytadan kiriting:',
        'en': '\u274c Invalid email format. Try again:',
    },
    'reg_email_exists': {
        'ru': '\u26a0\ufe0f Этот email уже зарегистрирован.\nИспользуйте /link чтобы привязать аккаунт.',
        'uz': '\u26a0\ufe0f Bu email allaqachon ro\'yxatdan o\'tgan.\n/link orqali akkauntni ulang.',
        'en': '\u26a0\ufe0f This email is already registered.\nUse /link to link your account.',
    },
    'reg_confirm': {
        'ru': '\U0001f4cb <b>Проверьте данные:</b>\n\n\U0001f464 Имя: <b>{name}</b>\n\U0001f4f1 Телефон: <b>{phone}</b>\n\U0001f4e7 Email: <b>{email}</b>\n\nВсё верно?',
        'uz': '\U0001f4cb <b>Ma\'lumotlarni tekshiring:</b>\n\n\U0001f464 Ism: <b>{name}</b>\n\U0001f4f1 Telefon: <b>{phone}</b>\n\U0001f4e7 Email: <b>{email}</b>\n\nTo\'g\'rimi?',
        'en': '\U0001f4cb <b>Check your info:</b>\n\n\U0001f464 Name: <b>{name}</b>\n\U0001f4f1 Phone: <b>{phone}</b>\n\U0001f4e7 Email: <b>{email}</b>\n\nAll correct?',
    },
    'btn_confirm': {
        'ru': '\u2705 Подтвердить',
        'uz': '\u2705 Tasdiqlash',
        'en': '\u2705 Confirm',
    },
    'btn_cancel': {
        'ru': '\u274c Отмена',
        'uz': '\u274c Bekor qilish',
        'en': '\u274c Cancel',
    },
    'reg_cancelled': {
        'ru': 'Регистрация отменена.',
        'uz': 'Ro\'yxatdan o\'tish bekor qilindi.',
        'en': 'Registration cancelled.',
    },
    'reg_success': {
        'ru': '\u2705 <b>Аккаунт создан!</b>\n\n\U0001f4e7 Email: <code>{email}</code>\n\U0001f511 Пароль: <code>{password}</code>\n\n\u26a0\ufe0f Сохраните пароль! Он нужен для входа на сайте.\nВы уже будете получать уведомления о заказах.',
        'uz': '\u2705 <b>Akkaunt yaratildi!</b>\n\n\U0001f4e7 Email: <code>{email}</code>\n\U0001f511 Parol: <code>{password}</code>\n\n\u26a0\ufe0f Parolni saqlang! Saytga kirish uchun kerak.\nEndi buyurtmalar haqida xabar olasiz.',
        'en': '\u2705 <b>Account created!</b>\n\n\U0001f4e7 Email: <code>{email}</code>\n\U0001f511 Password: <code>{password}</code>\n\n\u26a0\ufe0f Save this password! You need it to log in.\nYou will now receive order notifications.',
    },

    # ── Location ──────────────────────────────────────────
    'location_received': {
        'ru': '\U0001f4cd <b>Геолокация получена</b>\n\nЭти координаты будут использованы при оформлении заказа.',
        'uz': '\U0001f4cd <b>Geolokatsiya qabul qilindi</b>\n\nBu koordinatalar buyurtma rasmiylashtirishda ishlatiladi.',
        'en': '\U0001f4cd <b>Location received</b>\n\nThese coordinates will be used for delivery.',
    },
    'location_no_account': {
        'ru': 'Сначала привяжите аккаунт: /link или /register',
        'uz': 'Avval akkauntni ulang: /link yoki /register',
        'en': 'Link your account first: /link or /register',
    },

    # ── General ───────────────────────────────────────────
    'cancelled': {
        'ru': 'Действие отменено.',
        'uz': 'Amal bekor qilindi.',
        'en': 'Action cancelled.',
    },
    'multiple_accounts': {
        'ru': 'Найдено несколько аккаунтов. Уточните email.',
        'uz': 'Bir nechta akkaunt topildi. Emailni aniqlashtiring.',
        'en': 'Multiple accounts found. Please specify email.',
    },
    'btn_register_new': {
        'ru': '\U0001f4dd Зарегистрироваться',
        'uz': '\U0001f4dd Ro\'yxatdan o\'tish',
        'en': '\U0001f4dd Register',
    },
    'go_to_site': {
        'ru': '\U0001f310 Перейти на сайт',
        'uz': '\U0001f310 Saytga o\'tish',
        'en': '\U0001f310 Go to site',
    },
}


def t(key: str, lang: str = 'ru', **kwargs) -> str:
    """Get translated text. Falls back to Russian."""
    text_dict = TEXTS.get(key, {})
    text = text_dict.get(lang, text_dict.get('ru', key))
    if kwargs:
        text = text.format(**kwargs)
    return text