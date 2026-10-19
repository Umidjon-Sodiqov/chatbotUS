"""
keep_alive.py — Render.com va boshqa bulutli xostinglar uchun veb-server

Render bepul Web Service rejimida port talab qiladi. Bu modul:
  1. HTTP health-check serverni background thread da ishga tushiradi
     (UptimeRobot yoki Render o'zi bu URL ga ping yuborishi uchun)
  2. Bot o'ziga-o'zi ping yuborib sleep mode ga tushmasligini ta'minlaydi
     (RENDER_URL .env da bo'lsa, tashqi servis shart emas)

Zero dependency — faqat Python standart kutubxonasidan foydalanadi.
"""

import os
import time
import logging
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is running 24/7! Status: OK")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

    def log_message(self, format, *args):
        # Konsol loglarini keraksiz so'rovlar bilan to'ldirmaslik uchun
        return


def run_server(port: int):
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info("Veb-server ishga tushdi | Port: %s", port)
        server.serve_forever()
    except Exception as e:
        logger.warning("Veb-serverni ishga tushirishda ogohlantirish: %s", e)


def start_keep_alive():
    """Veb-serverni alohida oqimda (background thread) ishga tushiradi"""
    port = int(os.getenv("PORT", 8080))
    t = threading.Thread(target=run_server, args=(port,), daemon=True)
    t.start()


# ─── O'z-o'ziga ping (Self-ping) ──────────────────────────────────────────────

def _self_ping_loop(url: str, interval: int):
    """
    Har `interval` soniyada `url` ga GET so'rov yuboradi.
    Xato bo'lsa jim o'tadi — bot ishlashda davom etadi.
    """
    logger.info("Self-ping boshlandi | URL: %s | Interval: %ss", url, interval)
    while True:
        time.sleep(interval)
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                logger.debug("Self-ping OK | Status: %s", resp.status)
        except Exception as exc:
            logger.debug("Self-ping xatosi (normal): %s", exc)


def start_self_ping(url: str, interval_seconds: int = 600):
    """
    Botni sleep mode ga tushirmaslik uchun o'z URL iga ping yuboruvchi
    background daemon thread ni ishga tushiradi.

    Args:
        url: Render.com tomonidan berilgan bot URL (masalan https://my-bot.onrender.com)
        interval_seconds: Ping oralig'i (soniyada). Default: 600 (10 daqiqa)
    """
    t = threading.Thread(
        target=_self_ping_loop,
        args=(url, interval_seconds),
        daemon=True,
        name="self-ping",
    )
    t.start()
