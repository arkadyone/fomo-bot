# telegram_poster.py
import os, requests, html
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def _escape(s: str) -> str:
    return html.escape(str(s), quote=False)

def send_telegram_message(text: str, chat_id: str = TELEGRAM_CHAT_ID):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    r = requests.post(f"{API}/sendMessage", json=payload, timeout=20)
    print("📤 Status code:", r.status_code)
    print("📩 Response:", r.text)
