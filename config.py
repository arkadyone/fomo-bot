from dotenv import load_dotenv
import os

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")