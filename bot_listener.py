from telegram.ext import Updater, CommandHandler
from telegram import ParseMode
from config import TELEGRAM_BOT_TOKEN
from claude_writer import generate_daily_report

#  /start
def start(update, context):
    chat_id = update.effective_chat.id
    first_name = update.effective_user.first_name
    context.bot.send_message(
        chat_id=chat_id,
        text=f"Hey, {first_name}! You subscbe for the Fomo Vynt bot 🥲\n Your first report will be ready on daily basis."
    )

# 
def send_report(update, context):
    chat_id = update.effective_chat.id
    report = generate_daily_report()
    context.bot.send_message(chat_id=chat_id, text=report, parse_mode=ParseMode.MARKDOWN)

def main():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("report", send_report))  # for manual testing

    print("🤖 Bot is running /start")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
