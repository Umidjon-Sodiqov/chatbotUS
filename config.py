"""
config.py — Bot konfiguratsiyasi
Bot token, admin ID, ish vaqti va rate limit sozlamalari
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Asosiy sozlamalar ────────────────────────────────────────────────────────

# Bot tokeni — BotFather dan olinadi
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Admin Telegram ID — barcha xabarlar shunga boradi
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))

# ─── Ish vaqti (UTC+5, Toshkent) ─────────────────────────────────────────────

WORK_START_HOUR: int = int(os.getenv("WORK_START_HOUR", "9"))   # 09:00
WORK_END_HOUR:   int = int(os.getenv("WORK_END_HOUR",   "23"))  # 23:00
# Ish kunlari: 0=Dushanba ... 6=Yakshanba
# Default: hafta davomida (0-6), o'zgartirishingiz mumkin
WORK_DAYS: list[int] = [0, 1, 2, 3, 4, 5, 6]

# ─── Rate limit (spam himoya) ─────────────────────────────────────────────────

ENABLE_RATE_LIMIT: bool = False  # Vaqtincha o'chirilgan (yoqish uchun True qiling)
RATE_LIMIT_MAX: int = int(os.getenv("RATE_LIMIT_MAX", "5"))   # max xabar soni
RATE_LIMIT_SEC: int = int(os.getenv("RATE_LIMIT_SEC", "60"))  # oyna (soniya)

# ─── Render.com self-ping (sleep modega tushmaslik uchun) ─────────────────────

# Render tomonidan berilgan URL (masalan: https://my-bot.onrender.com)
# Bo'sh qolsa, self-ping ishlamaydi (mahalliy ishga tushirishda kerak emas)
RENDER_URL: str = os.getenv("RENDER_URL", "")

# Ping oralig'i soniyada (default: 600 = 10 daqiqa)
# Render bepul rejimda 15 daqiqa faoliyat bo'lmasa sleep ga tushadi,
# shuning uchun 10 daqiqa yetarli
SELF_PING_INTERVAL: int = int(os.getenv("SELF_PING_INTERVAL", "600"))

# ─── Validatsiya ──────────────────────────────────────────────────────────────

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN .env faylida topilmadi!")

if not ADMIN_ID:
    raise ValueError("❌ ADMIN_ID .env faylida topilmadi!")
