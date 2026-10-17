"""
keep_alive.py — Render.com va boshqa bulutli xostinglar uchun veb-server

Render bepul Web Service rejimida port talab qiladi va UptimeRobot
orqali botni 24/7 uyg'oq (sleep mode ga tushirmasdan) saqlashga xizmat qiladi.
Zero dependency — faqat Python standart kutubxonasidan foydalanadi.
"""

import os
import logging
import threading
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
