import os
from dotenv import load_dotenv

load_dotenv()

# Discord credentials
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_APPLICATION_ID = os.getenv('DISCORD_APPLICATION_ID')

# Database configuration
DATABASE_NAME = 'discord_metrics.db'