"""
keyboards.py — Telegram klaviaturalari (Ko'p tilli: uz, ru, en)
"""

from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import messages as msg


# ─── Tugma matnlari lug'ati ───────────────────────────────────────────────────

BTN = {
    "send_msg": {
        "uz": "✍️ Murojaat yozish",
        "ru": "✍️ Написать обращение",
        "en": "✍️ Send message",
    },
    "share_phone": {
        "uz": "📞 Raqamni ulashish",
        "ru": "📞 Поделиться номером",
        "en": "📞 Share phone number",
    },
    "my_tickets": {
        "uz": "📋 Mening murojaatlarim",
        "ru": "📋 Мои обращения",
        "en": "📋 My tickets",
    },
    "my_info": {
        "uz": "👤 Ma'lumotlarim",
        "ru": "👤 Мои данные",
        "en": "👤 My profile",
    },
    "bot_info": {
        "uz": "ℹ️ Bot haqida",
        "ru": "ℹ️ О боте",
        "en": "ℹ️ About bot",
    },
    "change_lang": {
        "uz": "🌐 Tilni o'zgartirish",
        "ru": "🌐 Сменить язык",
        "en": "🌐 Change language",
    },
    "cancel": {
        "uz": "❌ Bekor qilish",
        "ru": "❌ Отмена",
        "en": "❌ Cancel",
    },
}


def _btn(key: str, lang: str = "uz") -> str:
    return BTN.get(key, {}).get(lang) or BTN.get(key, {}).get("uz", "")


# ─── Foydalanuvchi klaviaturalari ─────────────────────────────────────────────

def main_menu_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Asosiy menyu (raqam ulashish tugmasi bilan)"""
    buttons = [
        [KeyboardButton(_btn("share_phone", lang), request_contact=True)],
        [KeyboardButton(_btn("send_msg", lang)), KeyboardButton(_btn("my_tickets", lang))],
        [KeyboardButton(_btn("my_info", lang)),  KeyboardButton(_btn("bot_info", lang))],
        [KeyboardButton(_btn("change_lang", lang))],
    ]
    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
    )


def menu_without_contact(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Raqam ulashilgandan keyingi menyu"""
    buttons = [
        [KeyboardButton(_btn("send_msg", lang)), KeyboardButton(_btn("my_tickets", lang))],
        [KeyboardButton(_btn("my_info", lang)),  KeyboardButton(_btn("bot_info", lang))],
        [KeyboardButton(_btn("change_lang", lang))],
    ]
    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
    )


def category_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Murojaat kategoriyasini tanlash"""
    categories = msg.CATEGORY_NAMES.get(lang, msg.CATEGORY_NAMES["uz"])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💬 {categories['cat_question']}",  callback_data="cat_question")],
        [InlineKeyboardButton(f"🤝 {categories['cat_social']}",    callback_data="cat_social")],
        [InlineKeyboardButton(f"📢 {categories['cat_important']}", callback_data="cat_important")],
        [InlineKeyboardButton(f"🆘 {categories['cat_help']}",      callback_data="cat_help")],
    ])


def cancel_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Bekor qilish tugmasi"""
    return ReplyKeyboardMarkup(
        [[KeyboardButton(_btn("cancel", lang))]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def language_selection_keyboard() -> InlineKeyboardMarkup:
    """Til tanlash tugmalari"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="setlang_uz"),
            InlineKeyboardButton("🇷🇺 Русский",  callback_data="setlang_ru"),
        ],
        [
            InlineKeyboardButton("🇬🇧 English",  callback_data="setlang_en"),
        ]
    ])


# ─── Admin klaviaturalari ─────────────────────────────────────────────────────

def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Admin asosiy menyusi"""
    buttons = [
        [KeyboardButton("📋 Ochiq murojaatlar"), KeyboardButton("👥 Foydalanuvchilar")],
        [KeyboardButton("🚫 Bloklanganlar"),     KeyboardButton("📊 Statistika")],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def admin_ticket_keyboard(ticket_num: str, user_id: int, is_banned: bool = False) -> InlineKeyboardMarkup:
    """Har bir ticket xabarida admin uchun tugmalar"""
    ban_btn = (
        InlineKeyboardButton("🔓 Blokdan chiqarish", callback_data=f"unban_{user_id}_{ticket_num}")
        if is_banned else
        InlineKeyboardButton("🚫 Bloklash",          callback_data=f"ban_{user_id}_{ticket_num}")
    )
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yopish", callback_data=f"close_{ticket_num}"),
            ban_btn,
        ]
    ])


def admin_user_actions(user_id: int, is_banned: bool = False) -> InlineKeyboardMarkup:
    """Yangi foydalanuvchi xabarida admin uchun tugmalar"""
    if is_banned:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔓 Blokdan chiqarish", callback_data=f"unban_{user_id}")]
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Bloklash", callback_data=f"ban_{user_id}")]
    ])


def unban_button_inline(user_id: int) -> InlineKeyboardMarkup:
    """Bloklanganlar ro'yxatida tezkor ochish tugmasi"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔓 Blokdan chiqarish", callback_data=f"unban_{user_id}")]
    ])
