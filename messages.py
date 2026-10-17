"""
messages.py — Barcha xabar shablonlari (Ko'p tilli: uz, ru, en)

Formatlash: HTML (parse_mode=HTML)
"""

from typing import Optional


# ─── Tillar ───────────────────────────────────────────────────────────────────

SUPPORTED_LANGUAGES = ["uz", "ru", "en"]

LANG_NAMES = {
    "uz": "🇺🇿 O'zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

STATUS_EMOJI = {
    "pending":  "🟡",
    "answered": "🟢",
    "closed":   "⚫",
}

CATEGORY_EMOJI = {
    "cat_question":  "💬",
    "cat_social":    "🤝",
    "cat_important": "📢",
    "cat_help":      "🆘",
}

CATEGORY_NAMES = {
    "uz": {
        "cat_question":  "Oddiy savol",
        "cat_social":    "Tanishish / Muloqot",
        "cat_important": "Muhim xabar",
        "cat_help":      "Yordam kerak",
    },
    "ru": {
        "cat_question":  "Обычный вопрос",
        "cat_social":    "Знакомство / Общение",
        "cat_important": "Важное сообщение",
        "cat_help":      "Нужна помощь",
    },
    "en": {
        "cat_question":  "Question",
        "cat_social":    "Social / Chat",
        "cat_important": "Important",
        "cat_help":      "Need help",
    },
}


# ─── Ko'p tilli xabarlar lug'ati ──────────────────────────────────────────────

TEXTS = {
    "WELCOME_NEW": {
        "uz": (
            "👋 <b>Salom! Xush kelibsiz!</b>\n\n"
            "Bu bot orqali menga to'g'ridan-to'g'ri xabar yuborishingiz mumkin.\n\n"
            "╔══════════════════════════╗\n"
            "  🆔 Sizning ID: <code>{user_id}</code>\n"
            "╚══════════════════════════╝\n\n"
            "📌 <b>Qanday ishlaydi?</b>\n"
            "  • Xabaringizni yozing yoki «✍️ Murojaat yozish» tugmasini bosing\n"
            "  • Xabaringiz menga yetib keladi va tez orada javob qaytadi!\n\n"
            "📞 Telefon raqamingizni ham ulashishingiz mumkin (ixtiyoriy)"
        ),
        "ru": (
            "👋 <b>Здравствуйте! Добро пожаловать!</b>\n\n"
            "Через этого бота вы можете напрямую отправить мне сообщение.\n\n"
            "╔══════════════════════════╗\n"
            "  🆔 Ваш ID: <code>{user_id}</code>\n"
            "╚══════════════════════════╝\n\n"
            "📌 <b>Как это работает?</b>\n"
            "  • Напишите сообщение или нажмите «✍️ Написать обращение»\n"
            "  • Ваше сообщение поступит ко мне, и я скоро отвечу!\n\n"
            "📞 Вы также можете поделиться номером телефона (необязательно)"
        ),
        "en": (
            "👋 <b>Hello! Welcome!</b>\n\n"
            "Through this bot you can send me messages directly.\n\n"
            "╔══════════════════════════╗\n"
            "  🆔 Your ID: <code>{user_id}</code>\n"
            "╚══════════════════════════╝\n\n"
            "📌 <b>How it works?</b>\n"
            "  • Type your message or click «✍️ Send message»\n"
            "  • Your message arrives directly to me and I will reply soon!\n\n"
            "📞 You can also share your phone number (optional)"
        ),
    },

    "WELCOME_BACK": {
        "uz": (
            "👋 <b>Qaytib keldingiz!</b>\n\n"
            "🆔 Sizning ID: <code>{user_id}</code>\n\n"
            "Xabaringizni yozing yoki quyidagi menyudan foydalaning."
        ),
        "ru": (
            "👋 <b>С возвращением!</b>\n\n"
            "🆔 Ваш ID: <code>{user_id}</code>\n\n"
            "Напишите сообщение или воспользуйтесь меню ниже."
        ),
        "en": (
            "👋 <b>Welcome back!</b>\n\n"
            "🆔 Your ID: <code>{user_id}</code>\n\n"
            "Send your message or use the menu below."
        ),
    },

    "SELECT_CATEGORY": {
        "uz": "📂 <b>Murojaat turini tanlang:</b>\n\nPastdagi tugmalardan birini bosing 👇",
        "ru": "📂 <b>Выберите тему обращения:</b>\n\nНажмите одну из кнопок ниже 👇",
        "en": "📂 <b>Select category:</b>\n\nClick one of the buttons below 👇",
    },

    "TICKET_CREATED": {
        "uz": (
            "✅ <b>Murojaatingiz qabul qilindi!</b>\n\n"
            "🎫 Raqam: <code>#{ticket_num}</code>\n"
            "📂 Tur: {category_emoji} {category_name}\n\n"
            "Endi xabaringizni yuboring — matn, rasm, ovoz, fayl — barchasi qabul qilinadi!"
        ),
        "ru": (
            "✅ <b>Ваше обращение создано!</b>\n\n"
            "🎫 Номер: <code>#{ticket_num}</code>\n"
            "📂 Тема: {category_emoji} {category_name}\n\n"
            "Теперь отправьте сообщение — текст, фото, голос, файл — всё принимается!"
        ),
        "en": (
            "✅ <b>Ticket created!</b>\n\n"
            "🎫 Number: <code>#{ticket_num}</code>\n"
            "📂 Category: {category_emoji} {category_name}\n\n"
            "Now send your message — text, photo, voice, document!"
        ),
    },

    "MESSAGE_SENT": {
        "uz": "📨 <b>Xabar yuborildi!</b>\n\n🎫 <code>#{ticket_num}</code> murojaatingiz doirasida.\n⏳ Javob kutib turing...",
        "ru": "📨 <b>Сообщение отправлено!</b>\n\n🎫 По обращению: <code>#{ticket_num}</code>.\n⏳ Ожидайте ответа...",
        "en": "📨 <b>Message sent!</b>\n\n🎫 Ticket: <code>#{ticket_num}</code>.\n⏳ Waiting for reply...",
    },

    "REPLY_FROM_ADMIN": {
        "uz": "💬 <b>Javob:</b>\n\n{reply_text}\n\n━━━━━━━━━━━━━━━━━\n🎫 <code>#{ticket_num}</code>",
        "ru": "💬 <b>Ответ:</b>\n\n{reply_text}\n\n━━━━━━━━━━━━━━━━━\n🎫 <code>#{ticket_num}</code>",
        "en": "💬 <b>Reply:</b>\n\n{reply_text}\n\n━━━━━━━━━━━━━━━━━\n🎫 <code>#{ticket_num}</code>",
    },

    "TICKET_CLOSED_USER": {
        "uz": (
            "🔒 <b>Murojaatingiz yopildi.</b>\n\n"
            "🎫 <code>#{ticket_num}</code>\n"
            "✅ Muammo hal bo'ldi deb hisoblaymiz.\n\n"
            "Yana savol bo'lsa — istalgan vaqtda yangi xabar yuborishingiz mumkin!"
        ),
        "ru": (
            "🔒 <b>Ваше обращение закрыто.</b>\n\n"
            "🎫 <code>#{ticket_num}</code>\n"
            "✅ Считаем вопрос решенным.\n\n"
            "Если появятся вопросы — можете написать новое сообщение в любое время!"
        ),
        "en": (
            "🔒 <b>Ticket closed.</b>\n\n"
            "🎫 <code>#{ticket_num}</code>\n"
            "✅ Marked as resolved.\n\n"
            "If you have more questions — feel free to send a new message anytime!"
        ),
    },

    "CONTACT_RECEIVED": {
        "uz": "✅ <b>Telefon raqamingiz saqlandi!</b>\n\n📞 <code>{phone}</code>\n\nEndi xabar yuborishingiz mumkin 👇",
        "ru": "✅ <b>Ваш номер телефона сохранен!</b>\n\n📞 <code>{phone}</code>\n\nТеперь вы можете отправить сообщение 👇",
        "en": "✅ <b>Phone number saved!</b>\n\n📞 <code>{phone}</code>\n\nNow you can send a message 👇",
    },

    "MY_INFO": {
        "uz": (
            "👤 <b>Sizning ma'lumotlaringiz:</b>\n\n"
            "Ism: <b>{full_name}</b>\n"
            "Username: {username}\n"
            "🆔 Bot ID: <code>{user_id}</code>\n"
            "📞 Telefon: {phone}\n"
            "🌐 Til: {lang_display}\n"
            "📅 Qo'shilgan: <i>{joined_at}</i>"
        ),
        "ru": (
            "👤 <b>Ваши данные:</b>\n\n"
            "Имя: <b>{full_name}</b>\n"
            "Username: {username}\n"
            "🆔 Bot ID: <code>{user_id}</code>\n"
            "📞 Телефон: {phone}\n"
            "🌐 Язык: {lang_display}\n"
            "📅 Регистрация: <i>{joined_at}</i>"
        ),
        "en": (
            "👤 <b>Your profile:</b>\n\n"
            "Name: <b>{full_name}</b>\n"
            "Username: {username}\n"
            "🆔 Bot ID: <code>{user_id}</code>\n"
            "📞 Phone: {phone}\n"
            "🌐 Language: {lang_display}\n"
            "📅 Joined: <i>{joined_at}</i>"
        ),
    },

    "MY_TICKETS": {
        "uz": "📋 <b>Sizning murojaatlaringiz:</b>\n\n{ticket_list}",
        "ru": "📋 <b>Ваши обращения:</b>\n\n{ticket_list}",
        "en": "📋 <b>Your tickets:</b>\n\n{ticket_list}",
    },

    "MY_TICKETS_EMPTY": {
        "uz": "📭 Hali murojaat qilmagansiz.\n\nXabar yozing yoki «✍️ Murojaat yozish» tugmasini bosing!",
        "ru": "📭 У вас пока нет обращений.\n\nНапишите сообщение или нажмите «✍️ Написать обращение»!",
        "en": "📭 You don't have any tickets yet.\n\nType a message or click «✍️ Send message»!",
    },

    "BOT_INFO": {
        "uz": (
            "ℹ️ <b>Bot haqida</b>\n\n"
            "Bu bot orqali menga to'g'ridan-to'g'ri xabar yuborishingiz mumkin.\n\n"
            "📌 <b>Nimalar yuborsa bo'ladi?</b>\n"
            "  📝 Matn  |  📸 Rasm  |  🎥 Video\n"
            "  🎙 Ovoz  |  📄 Fayl  |  😄 Sticker\n\n"
            "🆔 Sizning ID: <code>{user_id}</code>"
        ),
        "ru": (
            "ℹ️ <b>О боте</b>\n\n"
            "Через этого бота вы можете напрямую отправить мне сообщение.\n\n"
            "📌 <b>Что можно отправить?</b>\n"
            "  📝 Текст  |  📸 Фото  |  🎥 Видео\n"
            "  🎙 Голос  |  📄 Файл  |  😄 Стикер\n\n"
            "🆔 Ваш ID: <code>{user_id}</code>"
        ),
        "en": (
            "ℹ️ <b>About bot</b>\n\n"
            "Through this bot you can directly send me messages.\n\n"
            "📌 <b>What can you send?</b>\n"
            "  📝 Text  |  📸 Photo  |  🎥 Video\n"
            "  🎙 Voice  |  📄 File  |  😄 Sticker\n\n"
            "🆔 Your ID: <code>{user_id}</code>"
        ),
    },

    "BANNED_MESSAGE": {
        "uz": "🚫 <b>Sizning akkauntingiz bloklangan.</b>\n\nBoshqa yo'l bilan murojaat qiling.",
        "ru": "🚫 <b>Ваш аккаунт заблокирован.</b>\n\nПожалуйста, свяжитесь другим способом.",
        "en": "🚫 <b>Your account has been banned.</b>\n\nPlease contact via another method.",
    },

    "WORKING_HOURS_OFF": {
        "uz": (
            "🌙 <b>Hozircha javob bera olmayman.</b>\n\n"
            "Faol vaqt: ⏰ {start}:00 – {end}:00\n\n"
            "Xabaringiz saqlanib qoldi — faol vaqtda javob beraman! 🙂"
        ),
        "ru": (
            "🌙 <b>Сейчас нерабочее время.</b>\n\n"
            "Рабочие часы: ⏰ {start}:00 – {end}:00\n\n"
            "Ваше сообщение сохранено — я отвечу в рабочее время! 🙂"
        ),
        "en": (
            "🌙 <b>Currently off-hours.</b>\n\n"
            "Active hours: ⏰ {start}:00 – {end}:00\n\n"
            "Your message is saved — I will reply during active hours! 🙂"
        ),
    },

    "SELECT_LANGUAGE": {
        "uz": "🌐 <b>Tilni tanlang / Выберите язык / Select language:</b>",
        "ru": "🌐 <b>Выберите язык / Tilni tanlang / Select language:</b>",
        "en": "🌐 <b>Select language / Tilni tanlang / Выберите язык:</b>",
    },

    "LANGUAGE_CHANGED": {
        "uz": "✅ Til <b>O'zbekcha</b>ga o'zgartirildi!",
        "ru": "✅ Язык успешно изменен на <b>Русский</b>!",
        "en": "✅ Language successfully changed to <b>English</b>!",
    },

    "USER_TEXT_MESSAGE": {
        "uz": "💬 <b>Yangi xabar</b> | 🎫 <code>#{ticket_num}</code>\n👤 {full_name}  {username}  🆔 <code>{user_id}</code>  🌐 <code>{lang_code}</code>\n━━━━━━━━━━━━━━━━━━━━━\n{user_text}",
        "ru": "💬 <b>Yangi xabar</b> | 🎫 <code>#{ticket_num}</code>\n👤 {full_name}  {username}  🆔 <code>{user_id}</code>  🌐 <code>{lang_code}</code>\n━━━━━━━━━━━━━━━━━━━━━\n{user_text}",
        "en": "💬 <b>Yangi xabar</b> | 🎫 <code>#{ticket_num}</code>\n👤 {full_name}  {username}  🆔 <code>{user_id}</code>  🌐 <code>{lang_code}</code>\n━━━━━━━━━━━━━━━━━━━━━\n{user_text}",
    },

    "CANCELLED": {
        "uz": "✅ Bekor qilindi.",
        "ru": "✅ Отменено.",
        "en": "✅ Cancelled.",
    },
}


# ─── Adminga xabarlar (O'zbek tilida) ─────────────────────────────────────────

NEW_USER_NOTIFICATION = """
🆕 <b>Yangi foydalanuvchi!</b>

👤 Ism: <b>{full_name}</b>
🔖 Username: {username}
🆔 ID: <code>{user_id}</code>
🌐 Til: {lang_display}
📞 Telefon: {phone}
📅 Qo'shilgan: <i>{joined_at}</i>
""".strip()

PHONE_UPDATED_NOTIFICATION = """
📞 <b>Foydalanuvchi raqam ulashdi!</b>

👤 <b>{full_name}</b> (<code>{user_id}</code>)
📞 <code>{phone}</code>
""".strip()

NEW_TICKET_NOTIFICATION = """
🎫 <b>Yangi murojaat!</b>
━━━━━━━━━━━━━━━━━━━━━
👤 {full_name}
🔖 {username}
🆔 ID: <code>{user_id}</code>  🌐 <code>{lang_code}</code>
━━━━━━━━━━━━━━━━━━━━━
📂 Tur: {category_emoji} <b>{category_name}</b>
🎟 Raqam: <code>#{ticket_num}</code>
🟡 Holat: Kutilmoqda
━━━━━━━━━━━━━━━━━━━━━
💡 Javob berish uchun xabarni <b>Reply</b> qiling.
""".strip()

USER_MESSAGE_HEADER = """
💬 <b>Xabar</b> | 🎫 <code>#{ticket_num}</code>
👤 {full_name}  {username}  🆔 <code>{user_id}</code>  🌐 <code>{lang_code}</code>
""".strip()

REPLY_SENT_CONFIRM = "✅ Javob yetkazildi → <code>{user_id}</code> | 🎫 <code>#{ticket_num}</code>"

TICKET_CLOSED_ADMIN = "🔒 <code>#{ticket_num}</code> murojaat yopildi."

OPEN_TICKETS_HEADER = "📋 <b>Ochiq murojaatlar</b> ({count} ta):\n\n"
OPEN_TICKET_ITEM = (
    "{status} <code>#{num}</code> | {cat_emoji} {cat}\n"
    "   👤 {name}  🆔 <code>{user_id}</code>\n"
    "   🕐 <i>{date}</i>\n\n"
)
OPEN_TICKETS_EMPTY = "✅ Hozircha barcha murojaatlar ko'rib chiqilgan!"

BAN_CONFIRM    = "🚫 Foydalanuvchi <code>{user_id}</code> bloklandi."
UNBAN_CONFIRM  = "✅ Foydalanuvchi <code>{user_id}</code> blokdan chiqarildi."
USER_NOT_FOUND = "❌ Foydalanuvchi topilmadi: <code>{user_id}</code>"

USERS_LIST_HEADER = "👥 <b>Foydalanuvchilar</b> (jami: {count})\n\n"
USER_LIST_ITEM = (
    "#{num}  🆔 <code>{user_id}</code>  👤 <b>{full_name}</b>  {username}  {status}\n"
)

STATS_MESSAGE = """
📊 <b>Statistika</b>

👥 Jami foydalanuvchilar: <b>{total_users}</b>
🚫 Bloklangan: <b>{banned}</b>

🎫 Jami murojaatlar: <b>{total_tickets}</b>
  🟡 Kutilmoqda: <b>{pending}</b>
  🟢 Javob berilgan: <b>{answered}</b>
  ⚫ Yopilgan: <b>{closed}</b>
""".strip()

ADMIN_HELP = """
🛠 <b>Admin buyruqlari:</b>

/open — Ochiq murojaatlar
/users — Foydalanuvchilar ro'yxati
/banned — Bloklangan foydalanuvchilar
/stats — Statistika
/close &lt;TKT-001&gt; — Murojaatni yopish
/ban &lt;user_id&gt; — Bloklash
/unban &lt;user_id&gt; — Blokdan chiqarish
/help — Ushbu yordam

💡 <b>Javob berish:</b> Xabarga <b>Reply</b> qiling.
""".strip()


# ─── Yordamchi funksiyalar ────────────────────────────────────────────────────

def get_text(key: str, lang: str = "uz", **kwargs) -> str:
    """Ko'p tilli xabarni formatlab qaytaradi"""
    lang_dict = TEXTS.get(key, {})
    template = lang_dict.get(lang) or lang_dict.get("uz", "")
    return template.format(**kwargs) if kwargs else template


def get_category_display(cat_key: str, lang: str = "uz") -> tuple[str, str]:
    """Kategoriya belgisi va nomini tilga qarab qaytaradi: (emoji, name)"""
    emoji = CATEGORY_EMOJI.get(cat_key, "📂")
    names = CATEGORY_NAMES.get(lang, CATEGORY_NAMES["uz"])
    name = names.get(cat_key, cat_key)
    return emoji, name


def format_username(username: Optional[str]) -> str:
    return f"@{username}" if username else "—"


def format_phone(phone: Optional[str]) -> str:
    return f"<code>{phone}</code>" if phone else "❓ Ulashilmagan"


def format_full_name(first: Optional[str], last: Optional[str]) -> str:
    parts = [p for p in [first, last] if p]
    return " ".join(parts) if parts else "Nomsiz"


def get_lang_display(lang_code: str) -> str:
    return LANG_NAMES.get(lang_code, lang_code.upper())
