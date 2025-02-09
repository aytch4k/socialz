import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API credentials
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE')
TELEGRAM_SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'telegram_scraper')

# Database configuration
DATABASE_NAME = 'telegram_metrics.db'