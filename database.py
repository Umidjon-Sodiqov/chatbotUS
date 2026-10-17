"""
database.py — SQLite bilan foydalanuvchilar va ticketlarni boshqarish

Jadvallar:
  users       — foydalanuvchilar
  tickets     — murojaatlar (#TKT-001 ...)
  rate_limits — spam himoya
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = "support_bot.db"


# ─── Ulanish ──────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """SQLite ulanish qaytaradi"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── Jadvallarni yaratish ─────────────────────────────────────────────────────

def init_db() -> None:
    """Ma'lumotlar bazasini yaratadi (birinchi ishga tushirishda)"""
    with get_connection() as conn:

        # Foydalanuvchilar
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                last_name   TEXT,
                phone       TEXT,
                state       TEXT DEFAULT 'idle',
                lang        TEXT DEFAULT 'uz',
                is_banned   INTEGER DEFAULT 0,
                joined_at   TEXT DEFAULT (datetime('now'))
            )
        """)

        # Eski bazaga ustun qo'shish (migratsiya)
        try:
            conn.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT 'uz'")
        except sqlite3.OperationalError:
            pass

        # Ticketlar
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_num   TEXT UNIQUE,
                user_id      INTEGER,
                category     TEXT,
                status       TEXT DEFAULT 'pending',
                created_at   TEXT,
                updated_at   TEXT,
                closed_at    TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Rate limit
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                user_id      INTEGER PRIMARY KEY,
                msg_count    INTEGER DEFAULT 0,
                window_start TEXT
            )
        """)

        # Admin xabarlarini user/ticket ga bog'lash
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_messages (
                admin_msg_id INTEGER PRIMARY KEY,
                user_id      INTEGER,
                ticket_num   TEXT,
                created_at   TEXT DEFAULT (datetime('now'))
            )
        """)

        conn.commit()
    logger.info("Ma'lumotlar bazasi tayyor")


# ─── Foydalanuvchilar ─────────────────────────────────────────────────────────

def upsert_user(
    user_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    phone: Optional[str] = None,
    lang: str = "uz",
) -> bool:
    """
    Foydalanuvchini qo'shadi yoki yangilaydi.
    Returns True — yangi foydalanuvchi.
    """
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT user_id, lang FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE users
                SET username = ?, first_name = ?, last_name = ?,
                    phone = COALESCE(?, phone),
                    lang = COALESCE(?, lang)
                WHERE user_id = ?
                """,
                (username, first_name, last_name, phone, lang, user_id),
            )
            conn.commit()
            return False
        else:
            conn.execute(
                """
                INSERT INTO users
                    (user_id, username, first_name, last_name, phone, lang, joined_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, username, first_name, last_name, phone, lang,
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            return True


def set_user_lang(user_id: int, lang: str) -> None:
    """Foydalanuvchi tilini saqlaydi"""
    with get_connection() as conn:
        conn.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
        conn.commit()


def get_user_lang(user_id: int) -> str:
    """Foydalanuvchi tilini qaytaradi (uz, ru, en)"""
    with get_connection() as conn:
        row = conn.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row and row["lang"]:
            return row["lang"]
        return "uz"


def update_phone(user_id: int, phone: str) -> None:
    """Telefon raqamini yangilaydi"""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id)
        )
        conn.commit()


def set_user_state(user_id: int, state: str) -> None:
    """Foydalanuvchi holatini yangilaydi: idle | selecting_category | chatting"""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET state = ? WHERE user_id = ?", (state, user_id)
        )
        conn.commit()


def get_user(user_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()


def is_banned(user_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT is_banned FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return bool(row and row["is_banned"])


def set_ban(user_id: int, banned: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET is_banned = ? WHERE user_id = ?",
            (int(banned), user_id),
        )
        conn.commit()


def get_banned_users() -> list:
    """Barcha bloklangan foydalanuvchilar ro'yxati"""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE is_banned = 1 ORDER BY joined_at DESC"
        ).fetchall()


def get_all_users() -> list:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users ORDER BY joined_at DESC"
        ).fetchall()


def count_users() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
        return row["cnt"] if row else 0


# ─── Ticketlar ────────────────────────────────────────────────────────────────

def _next_ticket_number() -> str:
    """Keyingi ticket raqamini yaratadi: TKT-001, TKT-002 ..."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM tickets"
        ).fetchone()
        num = (row["cnt"] if row else 0) + 1
        return f"TKT-{num:03d}"


def create_ticket(user_id: int, category: str) -> sqlite3.Row:
    """Yangi ticket yaratadi va qaytaradi"""
    ticket_num = _next_ticket_number()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tickets (ticket_num, user_id, category, status, created_at, updated_at)
            VALUES (?, ?, ?, 'pending', ?, ?)
            """,
            (ticket_num, user_id, category, now, now),
        )
        conn.commit()
        return conn.execute(
            "SELECT * FROM tickets WHERE ticket_num = ?", (ticket_num,)
        ).fetchone()


def get_ticket(ticket_num: str) -> Optional[sqlite3.Row]:
    """Ticket raqami bo'yicha qidiradi"""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM tickets WHERE ticket_num = ?", (ticket_num,)
        ).fetchone()


def get_ticket_by_id(ticket_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)
        ).fetchone()


def get_user_active_ticket(user_id: int) -> Optional[sqlite3.Row]:
    """Foydalanuvchining oxirgi ochiq ticketini qaytaradi"""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM tickets
            WHERE user_id = ? AND status IN ('pending', 'answered')
            ORDER BY created_at DESC LIMIT 1
            """,
            (user_id,),
        ).fetchone()


def get_user_tickets(user_id: int, limit: int = 5) -> list:
    """Foydalanuvchining so'nggi ticketlari"""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM tickets WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()


def update_ticket_status(ticket_num: str, status: str) -> None:
    """Ticket holatini yangilaydi: pending | answered | closed"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    closed_at = now if status == "closed" else None

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tickets
            SET status = ?, updated_at = ?, closed_at = COALESCE(?, closed_at)
            WHERE ticket_num = ?
            """,
            (status, now, closed_at, ticket_num),
        )
        conn.commit()


def get_open_tickets() -> list:
    """Barcha ochiq (pending/answered) ticketlar"""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT t.*, u.username, u.first_name, u.last_name
            FROM tickets t
            JOIN users u ON t.user_id = u.user_id
            WHERE t.status IN ('pending', 'answered')
            ORDER BY t.created_at ASC
            """
        ).fetchall()


def count_tickets_by_status() -> dict:
    """Holat bo'yicha ticket soni"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM tickets GROUP BY status"
        ).fetchall()
        return {row["status"]: row["cnt"] for row in rows}


# ─── Rate limit ───────────────────────────────────────────────────────────────

def get_rate_limit(user_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM rate_limits WHERE user_id = ?", (user_id,)
        ).fetchone()


def update_rate_limit(user_id: int, msg_count: int, window_start: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO rate_limits (user_id, msg_count, window_start)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE
            SET msg_count = ?, window_start = ?
            """,
            (user_id, msg_count, window_start, msg_count, window_start),
        )
        conn.commit()


# ─── Admin xabar xaritalash ───────────────────────────────────────────────────

def save_admin_message(admin_msg_id: int, user_id: int, ticket_num: Optional[str] = None) -> None:
    """Adminga yuborilgan xabarni qaysi foydalanuvchi/ticketga tegishli ekanligini saqlaydi"""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO admin_messages (admin_msg_id, user_id, ticket_num)
            VALUES (?, ?, ?)
            """,
            (admin_msg_id, user_id, ticket_num),
        )
        conn.commit()


def get_admin_message_target(admin_msg_id: int) -> Optional[sqlite3.Row]:
    """Admin Reply qilgan xabar qaysi user/ticketga tegishli ekanligini topadi"""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM admin_messages WHERE admin_msg_id = ?",
            (admin_msg_id,),
        ).fetchone()

