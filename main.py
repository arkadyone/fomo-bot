from claude_writer import generate_daily_report
from telegram_poster import send_telegram_message
from config import TELEGRAM_CHAT_ID

def run_looser_bot():
    print("🧠 Generating report...")
    text = generate_daily_report()

    print("📤 Send report to Telegram...")
    send_telegram_message(chat_id=TELEGRAM_CHAT_ID, text=text)

if __name__ == "__main__":
    run_looser_bot()