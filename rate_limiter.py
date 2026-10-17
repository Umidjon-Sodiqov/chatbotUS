"""
rate_limiter.py — Spam himoya moduli

Ishlash printsipi:
  Har bir foydalanuvchi uchun RATE_LIMIT_SEC soniyalik oyna ichida
  RATE_LIMIT_MAX ta xabardan ko'p yubora olmaydi.
"""

from datetime import datetime, timedelta
import database as db
import config


def is_rate_limited(user_id: int) -> bool:
    """
    Foydalanuvchi rate limit ga tushgan-mi?
    True  — bloklangan (ko'p xabar yuborgan)
    False — ruxsat bor
    """
    if not getattr(config, "ENABLE_RATE_LIMIT", False):
        return False

    now    = datetime.now()
    record = db.get_rate_limit(user_id)

    if not record:
        # Birinchi xabar — yozib qo'yamiz
        db.update_rate_limit(user_id, 1, now.strftime("%Y-%m-%d %H:%M:%S"))
        return False

    window_start = datetime.strptime(record["window_start"], "%Y-%m-%d %H:%M:%S")
    elapsed      = (now - window_start).total_seconds()

    if elapsed > config.RATE_LIMIT_SEC:
        # Oyna tugagan — yangi oyna boshlaydi
        db.update_rate_limit(user_id, 1, now.strftime("%Y-%m-%d %H:%M:%S"))
        return False

    if record["msg_count"] >= config.RATE_LIMIT_MAX:
        # Oyna ichida limit oshib ketdi
        return True

    # Oyna ichida, limit oshib ketmagan — sanani oshiramiz
    db.update_rate_limit(
        user_id,
        record["msg_count"] + 1,
        record["window_start"],
    )
    return False


def seconds_until_reset(user_id: int) -> int:
    """Foydalanuvchi qancha soniyadan keyin xabar yubora olishini qaytaradi"""
    record = db.get_rate_limit(user_id)
    if not record:
        return 0

    window_start = datetime.strptime(record["window_start"], "%Y-%m-%d %H:%M:%S")
    elapsed      = (datetime.now() - window_start).total_seconds()
    remaining    = config.RATE_LIMIT_SEC - elapsed

    return max(0, int(remaining))
