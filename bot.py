"""
bot.py — Telegram Support Bot (Ko'p tilli: uz, ru, en)

Xususiyatlar:
  - Telegram settings tilini avtomatik aniqlash (uz, ru, en)
  - Foydalanuvchi tilini qo'lda o'zgartirish imkoniyati
  - Barcha media turlari (rasm, video, ovoz, fayl...)
  - Ticket tizimi (#TKT-001)
  - Dinamik ban/unban tugmalari
  - Bloklanganlar ro'yxati (/banned)

Ishga tushirish:
    python bot.py
"""

import html
import logging
import re
from datetime import datetime
from typing import Optional

from telegram import Update, Message
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

import config
import database as db
import messages as msg
import rate_limiter as rl
import keep_alive
from keyboards import (
    main_menu_keyboard,
    menu_without_contact,
    category_keyboard,
    cancel_keyboard,
    language_selection_keyboard,
    admin_menu_keyboard,
    admin_ticket_keyboard,
    admin_user_actions,
    unban_button_inline,
)

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# ─── Yordamchi funksiyalar ────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID


def normalize_lang(code: Optional[str]) -> str:
    """Telegram til kodini qo'llab-quvvatlanadigan tilga o'giradi (uz, ru, en)"""
    if not code:
        return "uz"
    code = code.lower()
    if code.startswith("ru"):
        return "ru"
    if code.startswith("en"):
        return "en"
    if code.startswith("uz"):
        return "uz"
    # Agar boshqa til bo'lsa (de, fr, tr...) — xalqaro ingliz tili tanlanadi
    return "en"


def get_user_info(update: Update) -> dict:
    """Update dan foydalanuvchi ma'lumotini yig'adi va tilini aniqlaydi"""
    user = update.effective_user
    tg_lang = normalize_lang(user.language_code)

    # Foydalanuvchi bazada bormi va tili saqlanganmi?
    saved_lang = db.get_user_lang(user.id)
    lang = saved_lang if saved_lang else tg_lang

    return {
        "user_id":    user.id,
        "username":   user.username,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "full_name":  msg.format_full_name(user.first_name, user.last_name),
        "lang":       lang,
        "tg_lang":    tg_lang,
    }


def is_working_hours() -> bool:
    """Hozir ish vaqti ekanligini tekshiradi"""
    now = datetime.now()
    return (
        now.weekday() in config.WORK_DAYS
        and config.WORK_START_HOUR <= now.hour < config.WORK_END_HOUR
    )


async def notify_admin_new_user(
    context: ContextTypes.DEFAULT_TYPE, info: dict
) -> None:
    """Adminga yangi foydalanuvchi haqida xabar yuboradi"""
    user_db = db.get_user(info["user_id"])
    phone   = msg.format_phone(user_db["phone"] if user_db else None)

    sent_msg = await context.bot.send_message(
        chat_id    = config.ADMIN_ID,
        text       = msg.NEW_USER_NOTIFICATION.format(
            full_name    = info["full_name"],
            username     = msg.format_username(info["username"]),
            user_id      = info["user_id"],
            lang_display = msg.get_lang_display(info["lang"]),
            phone        = phone,
            joined_at    = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
        parse_mode   = ParseMode.HTML,
        reply_markup = admin_user_actions(info["user_id"]),
    )
    db.save_admin_message(sent_msg.message_id, info["user_id"])


async def send_ticket_to_admin(
    context: ContextTypes.DEFAULT_TYPE,
    ticket: object,
    info: dict,
) -> None:
    """Yangi ticket haqida adminga xabar yuboradi"""
    cat_emoji, cat_name = msg.get_category_display(ticket["category"], lang=info["lang"])

    sent_msg = await context.bot.send_message(
        chat_id    = config.ADMIN_ID,
        text       = msg.NEW_TICKET_NOTIFICATION.format(
            full_name      = info["full_name"],
            username       = msg.format_username(info["username"]),
            user_id        = info["user_id"],
            lang_code      = info["lang"].upper(),
            category_emoji = cat_emoji,
            category_name  = cat_name,
            ticket_num     = ticket["ticket_num"],
        ),
        parse_mode   = ParseMode.HTML,
        reply_markup = admin_ticket_keyboard(ticket["ticket_num"], info["user_id"]),
    )
    db.save_admin_message(sent_msg.message_id, info["user_id"], ticket["ticket_num"])


# ─── /start ───────────────────────────────────────────────────────────────────

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Foydalanuvchi /start bosganda:
      - Admin bo'lsa → admin panel
      - Yangi bo'lsa → Telegram tili bo'yicha bazaga saqlanadi
      - Barcha matnlar foydalanuvchi tilida chiqadi
    """
    info = get_user_info(update)
    is_new = db.upsert_user(
        info["user_id"], info["username"],
        info["first_name"], info["last_name"],
        lang=info["tg_lang"],
    )

    user_lang = db.get_user_lang(info["user_id"])
    info["lang"] = user_lang

    if is_admin(info["user_id"]):
        await update.message.reply_text(
            msg.ADMIN_HELP,
            parse_mode   = ParseMode.HTML,
            reply_markup = admin_menu_keyboard(),
        )
        return

    user_db = db.get_user(info["user_id"])
    keyboard = (
        menu_without_contact(user_lang)
        if (user_db and user_db["phone"])
        else main_menu_keyboard(user_lang)
    )

    if is_new:
        await notify_admin_new_user(context, info)
        welcome_text = msg.get_text("WELCOME_NEW", lang=user_lang, user_id=info["user_id"])
        logger.info(
            "Yangi foydalanuvchi: %s (ID: %s, Til: %s)",
            info["full_name"], info["user_id"], user_lang
        )
    else:
        welcome_text = msg.get_text("WELCOME_BACK", lang=user_lang, user_id=info["user_id"])

    db.set_user_state(info["user_id"], "idle")

    await update.message.reply_text(
        welcome_text,
        parse_mode   = ParseMode.HTML,
        reply_markup = keyboard,
    )


# ─── Kontakt (telefon raqam) ──────────────────────────────────────────────────

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi telefon raqamini ulashganda"""
    contact = update.message.contact
    info    = get_user_info(update)
    user_lang = info["lang"]

    if contact.user_id != info["user_id"]:
        await update.message.reply_text("❌ Faqat o'z raqamingizni ulashing.")
        return

    db.update_phone(info["user_id"], contact.phone_number)

    await update.message.reply_text(
        msg.get_text("CONTACT_RECEIVED", lang=user_lang, phone=contact.phone_number),
        parse_mode   = ParseMode.HTML,
        reply_markup = menu_without_contact(user_lang),
    )

    sent_msg = await context.bot.send_message(
        chat_id    = config.ADMIN_ID,
        text       = msg.PHONE_UPDATED_NOTIFICATION.format(
            full_name = info["full_name"],
            user_id   = info["user_id"],
            phone     = contact.phone_number,
        ),
        parse_mode = ParseMode.HTML,
    )
    db.save_admin_message(sent_msg.message_id, info["user_id"])


# ─── Kategoriya tanlash (Inline callback) ────────────────────────────────────

async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi kategoriya tanlaganda yangi ticket yaratadi"""
    query = update.callback_query
    await query.answer()

    info     = get_user_info(update)
    user_lang = info["lang"]
    cat_key  = query.data  # "cat_question" | "cat_social" | ...

    ticket = db.create_ticket(info["user_id"], cat_key)
    cat_emoji, cat_name = msg.get_category_display(cat_key, lang=user_lang)

    db.set_user_state(info["user_id"], "chatting")

    await query.edit_message_text(
        msg.get_text(
            "TICKET_CREATED",
            lang=user_lang,
            ticket_num=ticket["ticket_num"],
            category_emoji=cat_emoji,
            category_name=cat_name,
        ),
        parse_mode=ParseMode.HTML,
    )

    await send_ticket_to_admin(context, ticket, info)
    logger.info(
        "Yangi ticket: #%s (%s) — %s",
        ticket["ticket_num"], cat_name, info["full_name"],
    )


# ─── Murojaat yozish tugmasi ──────────────────────────────────────────────────

async def start_ticket_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'✍️ Murojaat yozish' tugmasi bosilganda kategoriya tanlash"""
    info = get_user_info(update)
    user_lang = info["lang"]
    await update.message.reply_text(
        msg.get_text("SELECT_CATEGORY", lang=user_lang),
        parse_mode   = ParseMode.HTML,
        reply_markup = category_keyboard(lang=user_lang),
    )


# ─── Tilni o'zgartirish ───────────────────────────────────────────────────────

async def change_language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """'🌐 Tilni o'zgartirish' tugmasi bosilganda"""
    info = get_user_info(update)
    user_lang = info["lang"]
    await update.message.reply_text(
        msg.get_text("SELECT_LANGUAGE", lang=user_lang),
        parse_mode   = ParseMode.HTML,
        reply_markup = language_selection_keyboard(),
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi tilni tanlaganda"""
    query = update.callback_query
    await query.answer()

    new_lang = query.data.split("_")[1]  # "setlang_ru" -> "ru"
    db.set_user_lang(query.from_user.id, new_lang)

    user_db = db.get_user(query.from_user.id)
    keyboard = (
        menu_without_contact(new_lang)
        if (user_db and user_db["phone"])
        else main_menu_keyboard(new_lang)
    )

    try:
        await query.message.delete()
    except Exception:
        pass

    await context.bot.send_message(
        chat_id      = query.from_user.id,
        text         = msg.get_text("LANGUAGE_CHANGED", lang=new_lang),
        parse_mode   = ParseMode.HTML,
        reply_markup = keyboard,
    )


# ─── Mening murojaatlarim ─────────────────────────────────────────────────────

async def my_tickets_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi o'z so'nggi murojaatlarini ko'radi"""
    info    = get_user_info(update)
    user_lang = info["lang"]
    tickets = db.get_user_tickets(info["user_id"], limit=5)

    if not tickets:
        await update.message.reply_text(
            msg.get_text("MY_TICKETS_EMPTY", lang=user_lang),
            parse_mode=ParseMode.HTML,
        )
        return

    ticket_list = ""
    for t in tickets:
        status_emoji     = msg.STATUS_EMOJI.get(t["status"], "❓")
        cat_emoji, cat   = msg.get_category_display(t["category"], lang=user_lang)
        ticket_list += f"{status_emoji} <code>#{t['ticket_num']}</code> — {cat_emoji} {cat} — <i>{t['created_at'][:10]}</i>\n"

    await update.message.reply_text(
        msg.get_text("MY_TICKETS", lang=user_lang, ticket_list=ticket_list),
        parse_mode=ParseMode.HTML,
    )


# ─── Ma'lumotlarim ────────────────────────────────────────────────────────────

async def my_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    info    = get_user_info(update)
    user_lang = info["lang"]
    user_db = db.get_user(info["user_id"])

    if not user_db:
        await update.message.reply_text("❌ /start ni bosing.")
        return

    await update.message.reply_text(
        msg.get_text(
            "MY_INFO",
            lang=user_lang,
            full_name    = info["full_name"],
            username     = msg.format_username(info["username"]),
            user_id      = info["user_id"],
            phone        = msg.format_phone(user_db["phone"] if user_db else None),
            lang_display = msg.get_lang_display(user_lang),
            joined_at    = user_db["joined_at"] if user_db else "—",
        ),
        parse_mode=ParseMode.HTML,
    )


# ─── Bot haqida ───────────────────────────────────────────────────────────────

async def bot_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    info = get_user_info(update)
    user_lang = info["lang"]
    await update.message.reply_text(
        msg.get_text("BOT_INFO", lang=user_lang, user_id=info["user_id"]),
        parse_mode=ParseMode.HTML,
    )


# ─── Foydalanuvchi xabari → Admin ────────────────────────────────────────────

async def user_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchidan kelgan xabarni bitta qilib adminga yuboradi"""
    info    = get_user_info(update)
    user_lang = info["lang"]
    message = update.message

    # ── 1. Bloklangan? ──
    if db.is_banned(info["user_id"]):
        await message.reply_text(
            msg.get_text("BANNED_MESSAGE", lang=user_lang),
            parse_mode=ParseMode.HTML,
        )
        return

    # ── 2. Rate limit? ──
    if config.ENABLE_RATE_LIMIT and rl.is_rate_limited(info["user_id"]):
        seconds = rl.seconds_until_reset(info["user_id"])
        await message.reply_text(
            msg.get_text("RATE_LIMITED", lang=user_lang, seconds=seconds),
            parse_mode=ParseMode.HTML,
        )
        return

    # ── 3. Ish vaqti? ──
    if not is_working_hours():
        await message.reply_text(
            msg.get_text(
                "WORKING_HOURS_OFF",
                lang=user_lang,
                start=config.WORK_START_HOUR,
                end=config.WORK_END_HOUR,
            ),
            parse_mode=ParseMode.HTML,
        )

    # ── 4. Faol ticket ──
    ticket = db.get_user_active_ticket(info["user_id"])
    if not ticket:
        ticket = db.create_ticket(info["user_id"], "cat_question")

    # ── 5. Adminga: foydalanuvchi ma'lumoti va xabarini bitta qilib yuborish ──
    lang_code = user_lang.upper()

    if message.text:
        # Matnli xabar: ma'lumotlar va matn bitta xabarda keladi
        combined_text = msg.TEXTS["USER_TEXT_MESSAGE"]["uz"].format(
            ticket_num = ticket["ticket_num"],
            full_name  = info["full_name"],
            username   = msg.format_username(info["username"]),
            user_id    = info["user_id"],
            lang_code  = lang_code,
            user_text  = html.escape(message.text),
        )
        sent_msg = await context.bot.send_message(
            chat_id    = config.ADMIN_ID,
            text       = combined_text,
            parse_mode = ParseMode.HTML,
        )
        db.save_admin_message(sent_msg.message_id, info["user_id"], ticket["ticket_num"])
    else:
        # Media xabarlar (rasm, video, fayl, ovoz...)
        header_text = msg.USER_MESSAGE_HEADER.format(
            ticket_num = ticket["ticket_num"],
            full_name  = info["full_name"],
            username   = msg.format_username(info["username"]),
            user_id    = info["user_id"],
            lang_code  = lang_code,
        )
        original_caption = html.escape(message.caption) if message.caption else ""
        combined_caption = (
            f"{header_text}\n━━━━━━━━━━━━━━━━━━━━━\n{original_caption}".strip()
            if original_caption else header_text
        )

        try:
            # Rasm/video/fayl bo'lsa, caption sifatida bitta xabarda yuborish
            copied = await context.bot.copy_message(
                chat_id      = config.ADMIN_ID,
                from_chat_id = message.chat_id,
                message_id   = message.message_id,
                caption      = combined_caption,
                parse_mode   = ParseMode.HTML,
            )
            if hasattr(copied, "message_id"):
                db.save_admin_message(copied.message_id, info["user_id"], ticket["ticket_num"])
        except Exception:
            # Caption qabul qilmaydigan tur bo'lsa (sticker, video note) — header + media
            header_msg = await context.bot.send_message(
                chat_id    = config.ADMIN_ID,
                text       = header_text,
                parse_mode = ParseMode.HTML,
            )
            db.save_admin_message(header_msg.message_id, info["user_id"], ticket["ticket_num"])

            copied = await context.bot.copy_message(
                chat_id      = config.ADMIN_ID,
                from_chat_id = message.chat_id,
                message_id   = message.message_id,
            )
            if hasattr(copied, "message_id"):
                db.save_admin_message(copied.message_id, info["user_id"], ticket["ticket_num"])

    # ── Foydalanuvchiga tasdiqlash ──
    await message.reply_text(
        msg.get_text("MESSAGE_SENT", lang=user_lang, ticket_num=ticket["ticket_num"]),
        parse_mode=ParseMode.HTML,
    )

    logger.info(
        "Xabar: %s (%s) → Admin | Ticket: #%s",
        info["user_id"], user_lang, ticket["ticket_num"],
    )


# ─── Admin → Foydalanuvchi (Reply) ───────────────────────────────────────────

async def admin_reply_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Admin userdan kelgan har qanday xabarga (header, rasm, ovoz, matn) Reply qilganda
    foydalanuvchiga javob yuboradi va ticket holatini 'answered' ga o'tkazadi.
    Javob xabari foydalanuvchining o'z tilida yuboriladi!
    """
    message = update.message
    replied = message.reply_to_message

    if not replied:
        return

    # ── 1. Bazadan xabar ID bo'yicha aniqlash (eng aniq yo'l) ──
    target_id  = None
    ticket_num = None

    mapping = db.get_admin_message_target(replied.message_id)
    if mapping:
        target_id  = mapping["user_id"]
        ticket_num = mapping["ticket_num"]

    # ── 2. Matn/Caption dan regex orqali qidirish (zaxira) ──
    if not target_id:
        target_text = (replied.text or "") + "\n" + (replied.caption or "")
        if target_text.strip():
            id_match  = re.search(r"🆔\s*(?:ID:)?\s*(\d+)", target_text)
            tkt_match = re.search(r"#(TKT-\d+)", target_text)
            if id_match:
                target_id = int(id_match.group(1))
            if tkt_match:
                ticket_num = tkt_match.group(1)

    # ── 3. Forward origin (PTB v21+) ──
    if not target_id and replied.forward_origin:
        origin = replied.forward_origin
        if hasattr(origin, "sender_user") and origin.sender_user:
            target_id = origin.sender_user.id

    if not target_id:
        await message.reply_text(
            "❌ Foydalanuvchi aniqlanmadi.\n"
            "💡 Foydalanuvchidan kelgan xabarga Reply qiling.",
            parse_mode=ParseMode.HTML,
        )
        return

    # ── Foydalanuvchi mavjudligini tekshirish ──
    user_db = db.get_user(target_id)
    if not user_db:
        await message.reply_text(
            msg.USER_NOT_FOUND.format(user_id=target_id),
            parse_mode=ParseMode.HTML,
        )
        return

    target_lang = db.get_user_lang(target_id)

    # ── Ticket aniqlanmasa — faol ticketni olamiz ──
    if not ticket_num:
        active = db.get_user_active_ticket(target_id)
        ticket_num = active["ticket_num"] if active else "—"

    # ── Javob yuborish (foydalanuvchi tilida) ──
    reply_text = message.text or message.caption or ""

    if reply_text:
        await context.bot.send_message(
            chat_id    = target_id,
            text       = msg.get_text(
                "REPLY_FROM_ADMIN",
                lang=target_lang,
                reply_text=reply_text,
                ticket_num=ticket_num,
            ),
            parse_mode = ParseMode.HTML,
        )
    else:
        # Media (rasm, ovoz, fayl...) — to'g'ri copy qilamiz
        await context.bot.copy_message(
            chat_id      = target_id,
            from_chat_id = message.chat_id,
            message_id   = message.message_id,
        )

    # ── Ticket holatini yangilash ──
    if ticket_num and ticket_num != "—":
        db.update_ticket_status(ticket_num, "answered")

    # ── Admin ga tasdiqlash ──
    await message.reply_text(
        msg.REPLY_SENT_CONFIRM.format(user_id=target_id, ticket_num=ticket_num),
        parse_mode=ParseMode.HTML,
    )
    logger.info("Admin javobi → %s (%s) | Ticket: #%s", target_id, target_lang, ticket_num)


# ─── Inline tugmalar (Callback) ───────────────────────────────────────────────

async def inline_button_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Inline callback handler: kategoriya | til | admin amallari"""
    query = update.callback_query
    data = query.data

    # ── Til tanlash (foydalanuvchi) ──
    if data.startswith("setlang_"):
        await language_callback(update, context)
        return

    # ── Kategoriya tanlash (foydalanuvchi) ──
    if data.startswith("cat_"):
        await category_callback(update, context)
        return

    # ── Admin tugmalari ──
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    if data.startswith("close_"):
        ticket_num = data[6:]  # "close_TKT-007" → "TKT-007"
        ticket     = db.get_ticket(ticket_num)

        if not ticket:
            await query.message.reply_text(f"❌ Ticket topilmadi: {ticket_num}")
            return

        db.update_ticket_status(ticket_num, "closed")
        db.set_user_state(ticket["user_id"], "idle")

        user_lang = db.get_user_lang(ticket["user_id"])

        # Foydalanuvchiga uning tilida xabar yuborish
        await context.bot.send_message(
            chat_id    = ticket["user_id"],
            text       = msg.get_text("TICKET_CLOSED_USER", lang=user_lang, ticket_num=ticket_num),
            parse_mode = ParseMode.HTML,
        )

        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass

        await query.message.reply_text(
            msg.TICKET_CLOSED_ADMIN.format(ticket_num=ticket_num),
            parse_mode=ParseMode.HTML,
        )
        logger.info("Ticket yopildi: #%s", ticket_num)

    elif data.startswith("ban_"):
        parts = data.split("_")
        user_id = int(parts[1])
        ticket_num = parts[2] if len(parts) > 2 else None

        db.set_ban(user_id, True)

        # Tugmani "Blokdan chiqarish" ga almashtiramiz
        if ticket_num:
            new_markup = admin_ticket_keyboard(ticket_num, user_id, is_banned=True)
        else:
            new_markup = admin_user_actions(user_id, is_banned=True)

        try:
            await query.edit_message_reply_markup(reply_markup=new_markup)
        except Exception:
            pass

        await query.message.reply_text(
            msg.BAN_CONFIRM.format(user_id=user_id),
            parse_mode=ParseMode.HTML,
        )

    elif data.startswith("unban_"):
        parts = data.split("_")
        user_id = int(parts[1])
        ticket_num = parts[2] if len(parts) > 2 else None

        db.set_ban(user_id, False)

        # Tugmani "Bloklash" ga almashtiramiz
        if ticket_num:
            new_markup = admin_ticket_keyboard(ticket_num, user_id, is_banned=False)
        else:
            new_markup = admin_user_actions(user_id, is_banned=False)

        try:
            await query.edit_message_reply_markup(reply_markup=new_markup)
        except Exception:
            pass

        await query.message.reply_text(
            msg.UNBAN_CONFIRM.format(user_id=user_id),
            parse_mode=ParseMode.HTML,
        )


# ─── Admin buyruqlari ─────────────────────────────────────────────────────────

async def open_tickets_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """/open — barcha ochiq murojaatlar"""
    if not is_admin(update.effective_user.id):
        return

    tickets = db.get_open_tickets()

    if not tickets:
        await update.message.reply_text(
            msg.OPEN_TICKETS_EMPTY, parse_mode=ParseMode.HTML
        )
        return

    text = msg.OPEN_TICKETS_HEADER.format(count=len(tickets))
    for t in tickets:
        status_emoji     = msg.STATUS_EMOJI.get(t["status"], "❓")
        cat_emoji, cat   = msg.get_category_display(t["category"], lang="uz")
        full_name        = msg.format_full_name(t["first_name"], t["last_name"])

        text += msg.OPEN_TICKET_ITEM.format(
            status    = status_emoji,
            num       = t["ticket_num"],
            cat_emoji = cat_emoji,
            cat       = cat,
            name      = full_name,
            user_id   = t["user_id"],
            date      = t["created_at"][:16],
        )

        if len(text) > 3500:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            text = ""

    if text.strip():
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def close_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/close TKT-001 — ticketni yopish"""
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("❌ Foydalanish: /close TKT-001")
        return

    ticket_num = context.args[0].upper()
    if not ticket_num.startswith("TKT-"):
        ticket_num = f"TKT-{ticket_num}"

    ticket = db.get_ticket(ticket_num)
    if not ticket:
        await update.message.reply_text(
            f"❌ Ticket topilmadi: <code>{ticket_num}</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    db.update_ticket_status(ticket_num, "closed")
    db.set_user_state(ticket["user_id"], "idle")

    user_lang = db.get_user_lang(ticket["user_id"])

    await context.bot.send_message(
        chat_id    = ticket["user_id"],
        text       = msg.get_text("TICKET_CLOSED_USER", lang=user_lang, ticket_num=ticket_num),
        parse_mode = ParseMode.HTML,
    )

    await update.message.reply_text(
        msg.TICKET_CLOSED_ADMIN.format(ticket_num=ticket_num),
        parse_mode=ParseMode.HTML,
    )


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/users — barcha foydalanuvchilar"""
    if not is_admin(update.effective_user.id):
        return

    users = db.get_all_users()
    if not users:
        await update.message.reply_text("Hali foydalanuvchi yo'q.")
        return

    text = msg.USERS_LIST_HEADER.format(count=len(users))
    for i, u in enumerate(users, 1):
        full_name = msg.format_full_name(u["first_name"], u["last_name"])
        text += msg.USER_LIST_ITEM.format(
            num       = i,
            user_id   = u["user_id"],
            full_name = full_name,
            username  = msg.format_username(u["username"]),
            status    = "🚫" if u["is_banned"] else "✅",
        )
        if len(text) > 3500:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            text = ""

    if text.strip():
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/ban <user_id>"""
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Foydalanish: /ban <user_id>")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Noto'g'ri ID.")
        return

    if not db.get_user(target_id):
        await update.message.reply_text(
            msg.USER_NOT_FOUND.format(user_id=target_id), parse_mode=ParseMode.HTML
        )
        return

    db.set_ban(target_id, True)
    await update.message.reply_text(
        msg.BAN_CONFIRM.format(user_id=target_id), parse_mode=ParseMode.HTML
    )


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/unban <user_id>"""
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Foydalanish: /unban <user_id>")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Noto'g'ri ID.")
        return

    db.set_ban(target_id, False)
    await update.message.reply_text(
        msg.UNBAN_CONFIRM.format(user_id=target_id), parse_mode=ParseMode.HTML
    )


async def banned_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/banned — bloklangan foydalanuvchilar ro'yxati va ularni ochish"""
    if not is_admin(update.effective_user.id):
        return

    banned_users = db.get_banned_users()
    if not banned_users:
        await update.message.reply_text("✅ Hozirda hech qanday bloklangan foydalanuvchi yo'q.")
        return

    await update.message.reply_text(
        f"🚫 <b>Bloklangan foydalanuvchilar ({len(banned_users)} ta):</b>",
        parse_mode=ParseMode.HTML,
    )

    for u in banned_users:
        full_name = msg.format_full_name(u["first_name"], u["last_name"])
        username  = msg.format_username(u["username"])
        text = (
            f"👤 <b>{full_name}</b> {username}\n"
            f"🆔 ID: <code>{u['user_id']}</code>"
        )
        await update.message.reply_text(
            text,
            parse_mode   = ParseMode.HTML,
            reply_markup = unban_button_inline(u["user_id"]),
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/stats — statistika"""
    if not is_admin(update.effective_user.id):
        return

    all_users    = db.get_all_users()
    total_users  = len(all_users)
    banned       = sum(1 for u in all_users if u["is_banned"])
    ticket_stats = db.count_tickets_by_status()

    await update.message.reply_text(
        msg.STATS_MESSAGE.format(
            total_users = total_users,
            banned      = banned,
            total_tickets = sum(ticket_stats.values()),
            pending     = ticket_stats.get("pending",  0),
            answered    = ticket_stats.get("answered", 0),
            closed      = ticket_stats.get("closed",   0),
        ),
        parse_mode=ParseMode.HTML,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help"""
    if is_admin(update.effective_user.id):
        await update.message.reply_text(
            msg.ADMIN_HELP,
            parse_mode   = ParseMode.HTML,
            reply_markup = admin_menu_keyboard(),
        )
    else:
        info = get_user_info(update)
        await update.message.reply_text(
            msg.get_text("BOT_INFO", lang=info["lang"], user_id=update.effective_user.id),
            parse_mode=ParseMode.HTML,
        )


# ─── Admin menyu / Reply dispatcher ──────────────────────────────────────────

async def admin_message_dispatcher(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Admin tomonidan kelgan xabarlarni turlariga ko'ra yo'naltiradi"""
    message = update.message
    text    = message.text or ""

    if text == "📋 Ochiq murojaatlar":
        await open_tickets_command(update, context)
    elif text == "👥 Foydalanuvchilar":
        await users_command(update, context)
    elif text == "🚫 Bloklanganlar":
        await banned_command(update, context)
    elif text == "📊 Statistika":
        await stats_command(update, context)
    elif message.reply_to_message:
        await admin_reply_handler(update, context)


# ─── Foydalanuvchi menyu tugmalari ───────────────────────────────────────────

async def user_menu_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Foydalanuvchi Reply Keyboard tugmalarini (barcha tillarda) qayta ishlaydi"""
    text = update.message.text
    info = get_user_info(update)
    user_lang = info["lang"]

    send_msg_variants = ["✍️ Murojaat yozish", "✍️ Написать обращение", "✍️ Send message"]
    tickets_variants  = ["📋 Mening murojaatlarim", "📋 Мои обращения", "📋 My tickets"]
    info_variants     = ["👤 Ma'lumotlarim", "👤 Мои данные", "👤 My profile"]
    about_variants    = ["ℹ️ Bot haqida", "ℹ️ О боте", "ℹ️ About bot"]
    lang_variants     = ["🌐 Tilni o'zgartirish", "🌐 Сменить язык", "🌐 Change language"]
    cancel_variants   = ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]

    if text in send_msg_variants:
        await start_ticket_handler(update, context)
    elif text in tickets_variants:
        await my_tickets_handler(update, context)
    elif text in info_variants:
        await my_info_handler(update, context)
    elif text in about_variants:
        await bot_info_handler(update, context)
    elif text in lang_variants:
        await change_language_handler(update, context)
    elif text in cancel_variants:
        db.set_user_state(update.effective_user.id, "idle")
        await update.message.reply_text(
            msg.get_text("CANCELLED", lang=user_lang),
            reply_markup=main_menu_keyboard(user_lang),
        )
    else:
        # Oddiy matn xabari — adminga yuboradi
        await user_message_handler(update, context)


# ─── Aplikatsiyani qurish ─────────────────────────────────────────────────────

def build_application() -> Application:
    """Barcha handlerlarni ro'yxatdan o'tkazadi"""
    app = Application.builder().token(config.BOT_TOKEN).build()

    # ── Barcha foydalanuvchilar buyruqlari ──
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help",  help_command))

    # ── Admin buyruqlari ──
    app.add_handler(CommandHandler("open",   open_tickets_command))
    app.add_handler(CommandHandler("close",  close_command))
    app.add_handler(CommandHandler("users",  users_command))
    app.add_handler(CommandHandler("banned", banned_command))
    app.add_handler(CommandHandler("ban",    ban_command))
    app.add_handler(CommandHandler("unban",  unban_command))
    app.add_handler(CommandHandler("stats",  stats_command))

    # ── Kontakt ──
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    # ── Inline tugmalar (kategoriya + til + admin amallar) ──
    app.add_handler(CallbackQueryHandler(inline_button_handler))

    # ── Admin xabarlari (menyu + reply) ──
    app.add_handler(
        MessageHandler(
            filters.User(config.ADMIN_ID) & ~filters.COMMAND,
            admin_message_dispatcher,
        )
    )

    # ── Foydalanuvchi xabarlari (menyu tugmalari + xabarlar) ──
    app.add_handler(
        MessageHandler(
            ~filters.User(config.ADMIN_ID) & ~filters.COMMAND & ~filters.CONTACT,
            user_menu_handler,
        )
    )

    return app


# ─── Ishga tushirish ──────────────────────────────────────────────────────────

def main() -> None:
    """Botni ishga tushiradi"""
    db.init_db()

    # Render.com va bulutli xostinglar uchun veb-serverni ishga tushirish (Sleep modega tushmaslik uchun)
    keep_alive.start_keep_alive()

    # Self-ping: bot o'ziga-o'zi so'rov yuboradi (tashqi servis shart emas)
    if config.RENDER_URL:
        keep_alive.start_self_ping(config.RENDER_URL, config.SELF_PING_INTERVAL)
        logger.info(
            "Self-ping yoqildi | Har %s daqiqada %s ga ping",
            config.SELF_PING_INTERVAL // 60,
            config.RENDER_URL,
        )
    else:
        logger.info("Self-ping o'chirilgan (RENDER_URL .env da yo'q)")

    app = build_application()

    logger.info("Bot ishga tushdi | Admin ID: %s", config.ADMIN_ID)
    logger.info("Ish vaqti: %s:00 – %s:00", config.WORK_START_HOUR, config.WORK_END_HOUR)
    rl_info = f"{config.RATE_LIMIT_MAX} xabar / {config.RATE_LIMIT_SEC}s" if config.ENABLE_RATE_LIMIT else "O'chirilgan (Disabled)"
    logger.info("Rate limit: %s", rl_info)
    logger.info("To'xtatish uchun: Ctrl+C")


    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
